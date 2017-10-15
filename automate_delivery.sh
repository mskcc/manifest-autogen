#!/bin/sh

source /ifs/work/pi/pipelineKickoff/config.sh
source /ifs/work/pi/lib/bash/b-log.sh
source $(dirname $0)/constants.sh
source $(dirname $0)/notification-config.sh
source $(dirname $0)/log-config.sh
source $(dirname $0)/rest-config.sh

timeNums=$1
timeUnits=$2

if [ -z "$timeNums" ]; then
    timeNums=16
    timeUnits="m"
fi

INFO "Running automated delivery script"

IDsDone=$($pythonPath $getIdsCmd --recentProjects -t $timeNums -tu $timeUnits)
restfulERROR=$?

if [ $restfulERROR -ne 0 ]; then
    ERROR "Restful error";
    INFO "$IDsDone";
    exit -1
fi

IFS=$'\n' read -rd ',' -a ids <<< "$IDsDone"
INFO "Delivered projects: ${ids[*]}"

cd $createManifestPath
createManifestJar=${createManifestPath}/pipeline-kickoff-${version}.jar
INFO "Create Manifest path: ${createManifestJar}"

for id in $IDsDone
do
    INFO "Beginning of pipeline pulling for ${id}"

    output=$($javaPath -jar ${jvmParams} $createManifestJar -p ${id} -o output)
    echo "$output" >> $logFile

    INFO "End of pipeline pulling for ${id}"
    echo "-----------------------------------------------------" >> $logFile
done

cd $curDir


