# autogen-delivered-projects
This will generate manifest/project files for projects recently delivered in the LIMS

## Prerequisites:
- Access to the LIMS restful service
- Access to the Create Manifest Sheet java application

## Setup:
In the main repo directory, add the following to a file named `constants.sh` and fill in the variables for your setup: 
```
today=$(date +%Y_%m_%d)

#paths
draftsDir=""
createManifestDir=""
jaPath=""
pyPath=""

#today is here to fill out logFile filename (log${today}.txt)
logFile=""

cdir=$(dirname $0)
getIdsCmd="$cdir/restful/pullInformationFromLIMS.py"

#email address to send emails if there are errors
to=""
```

In the restful directory, create a file named `Connect.txt` with the first line of the file containing the LIMS restful service username and the second line containing the corresponding password. 

Also in the restful directory create a file named `constants.py` with the lines that follow:
```
baseUrl= ''
archivePath = ''
```
baseUrl is the url to the restful service
archivePath is our path to where the fastqs are stored

## How to Run
`./automate_delivery.sh <number of time units> <time unit>`
Time unit options are m, d, w, y (minute, day, week, year)
`./automate_delivery.sh 1 d`    Will run create manifest sheet on all projects delivered in the last 1 day
`./automate_delivery.sh 12 m`   Will run create manifest sheet on all projects delivered in the last 12 minutes

## Output
Output will go to `draftsDir` specified in constants.sh
Output of the create manifest sheet will be printed to `logFile`
Each project can only have one type of "pairedness" (single end or paired end). Otherwise an e-mail will be sent to the email provided in the constants.sh

