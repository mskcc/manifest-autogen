import urllib2
import argparse
import datetime
import base64
import json 
import glob
import os
import sys
import re
import getpass
from constants import *

binDir=os.path.dirname(sys.argv[0])

def getParsedArgs():
    parser=argparse.ArgumentParser()
    parser.add_argument("-d","--date",help="Filter by date (format 2016.07.15 or 2016_07_15)")
    parser.add_argument("-b","--batch",help="Filter by that batch number (delivery number)")
    parser.add_argument("-o","--output",help="Output Directory")
    parser.add_argument("-p","--projID",help="Project Id")
    parser.add_argument("-t","--time",help="Get recent deliveries from this time period")
    parser.add_argument("-tu","--timeUnit",help="Unit of time for -t option")
    parser.add_argument("--mapping", action="store_true", help="Print mapping file function")
    parser.add_argument("--recentProjects", action="store_true", help="Get recently delivered project info")
    return parser.parse_args()
    
def checkProjID(projID):
    exit = False
    if '*'in projID:
        print "Wildcard not allowed in request ID"
        exit = True;
    parts = projID.split("_")
    if not re.match('(\d){5}',parts[0]):
        print "Project ID should start with 5 digits.\n"
        exit = True;
    if len(parts) > 1:
        if not re.match('[A-Z]*', parts[1]):
            print "Malformed project id.\n"
            exit = True
    if len(parts) > 2: 
        print "Project ID should only have one underscore!\n"
        exit = True
    if exit:
        print "Correct project ID format: Five digits, one underscore, and a number of captial letters (01234_AC)"
    return
        
def saveDate(date):
    try:
        date1 = datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        try:
            date1 = datetime.datetime.strptime(date, '%Y.%m.%d')
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD or YYYY.MM.DD")
            sys.exit(-1)
    return date1

def checkBatch(batch):
    if not batch.isdigit():
       print "Batch should be an integer\n"
       sys.exit(-1)
       
def checkOutDir(output):
    if not os.path.isdir(output):
        print "Output should be a directory that is already created."
        sys.exit(-1)

def checkTime(time):
    if not time.isdigit():
        print "Time should be an integer\n"
        sys.exit(-1)

def checkTimeUnit(timeUnit):
    timeUnitOptions = ['d', 'w', 'm', 'y']
    if timeUnit not in timeUnitOptions:
        print "[ERROR] invalid time unit. Options are " + ", ".join(timeUnitOptions) + " \n"
        sys.exit(-1)

def getQueryResult (query):
    ## add to auth_header
    with(open(binDir + "/Connect.txt")) as connectInfo: 
        username = connectInfo.readline().strip()
        password = connectInfo.readline().strip()
    authheader = "Basic " + base64.b64encode(username + ":" + password)
    req= urllib2.Request(query)
    req.add_header("Authorization", authheader) 
    req.add_header("Content-Type", "application/json") 
    response = urllib2.urlopen(req)
    results = json.loads(response.read())

    try:
        if(results['restStatus'] != "SUCCESS"):
                print "[WARNING] Rest status not success: " + results['restStatus']
    except TypeError:
        try: 
            for r in results:
                if(r['restStatus'] != "SUCCESS"):
                    print "[WARNING] Rest status not success: " + r['restStatus']
        except TypeError:
            raise TypeError("[ERROR] cannot find restStatus in json output!")
            sys.exit(-1)

    return(results)

def recentDelProjects(timeVal = 1, unitVal='d', quiet=0):
    # First get new projects
    projList = list();
    q1 = baseUrl + 'getRecentDeliveries?time=' + str(timeVal) + '&units=' + unitVal
    projectList = getQueryResult(q1)
    for proj in projectList:
        request = proj['requestId']
        datesDelivered = proj['deliveryDate']
        projList.append(str(request)) #"deliveryDate: " + ", ".join(datesDelivered) + "\n"
        if len(datesDelivered) > 1 and not quiet:
            print "MULTIPLE DELIVERIES"
        # Next grab all QC info from get projQC
        q2 = baseUrl + 'getProjectQc?project=' + request
        projQC = getQueryResult(q2)
    return projList

##
##  mostRecentDate = sorted(datesDelivered)[-1]
##


def findFastqPath(projID, sname, run, extID=""):
    runDirs = glob.glob(archivePath + "/" + run + "*/Project_*" + projID[1:] + "/Sample_" + sname + "_IGO_" + extID + "*")
    if len(runDirs) == 1:
        directory=runDirs[0]
        if os.path.isdir(directory):
            return directory
    elif len(runDirs) > 1:
        print "[ERROR] than one folder for this sample in this run: " + runDirs
        sys.exit(-1)
    runDirs = glob.glob(archivePath + "/" + run + "*/Project_*" + projID[1:] + "/Sample_" + sname + "_IGO_*")
    if len(runDirs) == 1:
        directory=runDirs[0]
        if os.path.isdir(directory):
             print "[WARNING] fastq sample has different IGO ID than in sample qc records (" + extID + "): " + directory + "\n"
             return directory
    else:
        print "[ERROR] No fastq found for " + sname + " run: " + run + "\n"
        sys.exit(-1)
        
def findPEorSE(path):
    contents= os.listdir(path)
    pattern = re.compile('.*_L(\d){3}_R2_(\d){3}.fastq.gz$')
    matches = [m.group(0) for l in contents for m in [pattern.search(l)] if m]
    if len(matches) > 0:
        return "PE";
    else:
        pattern = re.compile('.*_L(\d){3}_R1_(\d){3}.fastq.gz$')
        matches = [m.group(0) for l in contents for m in [pattern.search(l)] if m]
        if len(matches) > 0:
            return "SE"
    print "[ERROR] Malformed fastq files in path " + path + "\n"
    return "UNKNOWN"

#
# IGO id's get a _1 or _2 added to the end of itself everythign it is "aliquoted" 
# This shoudl strip that down to the base ID.
#
def truncateID (longID):
    pattern = re.compile('((\d){5}_?([A-Za-z])*)_(\d)+')
    try:
        igoID = pattern.search(longID).group(0)
        return igoID
    except AttributeError:
        raise AttributeError("[ERROR] Malformed base(igo) ID: " + longID + ". Please contact someone for help!") 
        sys.exit(-1)

# This method will grab all delivery and sample QC info.
# I will print out mapping file based on other input (date/batch). 
def projectMappingFile(uname, projID, date=None, outDir=".", batch=None):
    #q1 = baseUrl + 'getProjectQc?project=' + projID
    q1 = baseUrl + 'getPassingSamplesForProject?project=' + projID + '&user=' + uname
    if date:
        q1 += '&year=' + str(date.year) + '&month=' + str(date.month) + '&day=' + str(date.day) 
    
    qcInfo = getQueryResult(q1) 
    
    fn = outDir + "/Proj_" + projID + "_sample_mapping_" + datetime.datetime.now().strftime("%Y_%m_%d") + ".txt"
    mappingFile = open( fn , 'w+')

    #if len(qcInfo) > 1 :
    #    print "[WARNING] List of requests should be 1, but is actually " + str(len(qcInfo)) + ". Only grabbing first request."
    info=qcInfo
   
    for samp in info['samples']:
        cmoID=samp['cmoId']
        extID = truncateID(samp['baseId'])  
        qcRec = samp['basicQcs'][0]
        run = qcRec['run']
        qc_status = qcRec['qcStatus']
        if qc_status != "Passed":
            continue
        sname = samp['cmoId']
        if(cmoID != sname):
            print "Sample has been renamed: old: " + sname + " new: " + cmoID
        # search for run ID directories. If more than one is found sort, and grab the largest(With new archiving, this will have to change).
        path = findFastqPath(projID, sname, run, extID)
        ended = findPEorSE(path)
        mappingFile.write("\t".join(["_1", cmoID, run, path, ended]) + "\n")
            
        
if __name__ == '__main__':

    uname = getpass.getuser();
    args = getParsedArgs()

    if not args.recentProjects and not args.mapping: 
        print "[ERROR] You must choose either --recentProjects or --mapping\n"
        sys.exit(-1)
    
    if args.mapping and not args.recentProjects:
        batch=date=None
        output="."
        if not args.projID:
            print "[ERROR] You must give project id with -p or --projID]\n"
            sys.exit(-1)
        checkProjID(args.projID)
        if args.date:
            date=saveDate(args.date)
        if args.batch:
            checkBatch(args.batch)
            batch = args.batch
        if args.output:
            checkOutDir(args.output)
            output = (args.output).rstrip("/")
        projectMappingFile(uname, args.projID, date, output, batch)
    elif args.recentProjects and not args.mapping:
        # Both time and time units are optional, but if one is used the other must be sued
        time = '1'
        timeUnit = 'd'
        if args.time and args.timeUnit:
            checkTime(args.time)
            time = args.time
            checkTimeUnit(args.timeUnit)
            timeUnit = args.timeUnit
        elif not args.time and not args.timeUnit:
            pass
        else:
            print"[ERROR] Must use both Time and Time unit options when using one.\n"
            sys.exit(-1)
        projIDs = recentDelProjects(time, timeUnit, 1)
        for p in projIDs:
            print  p 
    else:
        time = '1'
        timeUnit = 'd'
        batch=date=None
        output='.'
        if args.time and args.timeUnit:
            checkTime(args.time)
            time = args.time
            checkTimeUnit(args.timeUnit)
            timeUnit = args.timeUnit
        if args.output:
            checkOutDir(args.output)
            output = (args.output).rstrip("/")
        projIDs = recentDelProjects(time, timeUnit)
        for p in projIDs:
            print "[LOG] Grabbing mapping file for project " + p ;
            projectMappingFile(uname, p, date, output, batch)

 
