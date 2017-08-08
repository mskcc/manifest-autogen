
curDir=$(pwd)
userID=$(whoami)

#assigning all host/user/date specific variables
source $(dirname $0)/constants.sh

subject="CreateManifest results for Project ${id}"
from="${userID}@cbio.mskcc.org"
msg="Alert: Project ${id} as at least one sample has more than one pairedness. Please check."
bad_samples="";

timeNums=$1
timeUnits=$2

if [ -z "$timeNums" ]; then
    timeNums=16
    timeUnits="m"
fi

checkPairedness(){
    id=$1
    mappingFile="${draftsDir}/Proj_${id}_sample_mapping.txt"
    if [ -e $mappingFile ]
    then
        sampleNames=$(awk '{print $2}' ${mappingFile} | sort | uniq )
        for samp in $sampleNames
        do
            pairedness=$(awk -v sample="$samp" ' BEGIN {FS="\t"} if($2 = sample) { print $5 } ' $mappingFile | sort | uniq | wc -l)
            
            if [ $pairedness -ne 1 ]
            then
                # ALERT!
                #add samples to a variable
                bad_samples="${bad_samples} $samp"
            fi 
        done
        if [ ${#myvar} -gt 0 ]
        then
            msg="${msg} ${bad_samples}"
            echo $msg
            mailCMD="subject:${subject}\nfrom:{$from}\nto:${to},${pmEmail}\n${msg}"
            echo -e "${mailCMD}"| sendmail -t
        fi
    fi

}

# get the project ids that have been delivered recently
IDsDone=$($pyPath $getIdsCmd --recentProjects -t $timeNums -tu $timeUnits)

restfulERROR=$?

if [ $restfulERROR -ne 0 ]; then
    echo "[ERROR] restful error";
    echo "$IDsDone";
    exit -1
fi

if [ ! -e $logFile ]
then
    touch $logFile
    chmod 664 $logFile
fi

cd $createManifestDir
## For each id, put through manifest puller
for id in $IDsDone
do
    now=$(date +%Y_%m_%d:%H:%M:%S)
    #echo "############################" >> $logFile
    echo "Beginning of pipeline pulling for ${id}: ${now}" >> $logFile
    #echo "############################" >> $logFile
    
    output=$($jaPath -cp libs/*:build/classes/main:build/resources/main org.mskcc.kickoff.lims.CreateManifestSheet -p ${id})
    
    echo "$output" >> $logFile
    
    # CHECK FOR PAIREDNESS
    checkPairedness "$id"
    
    now=$(date +%Y_%m_%d:%H:%M:%S)
    #echo "############################" >> $logFile
    echo "End of pipeline pulling for ${id}: ${now}" >> $logFile
    echo "############################" >> $logFile


done

cd $curDir


