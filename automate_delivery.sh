#!/bin/sh

source /ifs/work/pi/pipelineKickoff/config.sh
source /ifs/work/pi/lib/bash/b-log.sh

curDir=$(dirname $0)

source $curDir/constants.sh
source $curDir/notification-config.sh
source $curDir/log-config.sh
source $curDir/rest-config.sh

cd $curDir

getFileStatus() {
    if [ ! -f ${outputPath}/Proj_${1}/${2} ]; then
	fileStatus+=$"\n\t :error:"
    else
	fileStatus+=$"\n\t :success:"
    fi

    fileStatus+=${2}
    echo "$fileStatus"
}

sendNotification() {
    if [ -z "$channel" ];then
        WARN "Channel not set thus notification won't be sent"
        return
    fi

    if [ -z "$username" ];then
        WARN "Username not set thus notification won't be sent"
        return
    fi

    if [ -z "$webhookUrl" ];then
        WARN "Channel not set thus notification won't be sent"
        return
    fi

    filesStatus=$(getFileStatus $1 "Proj_${1}_sample_mapping.txt")	
    filesStatus+=$(getFileStatus $1 "Proj_${1}_sample_pairing.txt")	
    filesStatus+=$(getFileStatus $1 "Proj_${1}_sample_grouping.txt")	
    filesStatus+=$(getFileStatus $1 "Proj_${1}_request.txt")	

    text=":boom: Manifest files generated for project: *${1}* :boom: ${filesStatus}"

    DEBUG "Sending notification to channel: ${channel}"
    curl -X POST --data-urlencode "payload={\"channel\": \"${channel}\", \"username\": \"${username}\", \"text\": \"${text}\", \"icon_emoji\": \":kingjulien:\"}" ${webhookUrl}
}

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

createManifestJar=${createManifestPath}/pipeline-kickoff-${version}.jar
INFO "Create Manifest path: ${createManifestJar}"

for id in $IDsDone
do
    INFO "Beginning of pipeline pulling for ${id}"

    output=$($javaPath -jar ${jvmParams} $createManifestJar -p ${id} ${manifestArgs})
    echo "$output" >> $logFile

    sendNotification $id

    INFO "End of pipeline pulling for ${id}"
    echo "-----------------------------------------------------" >> $logFile
done


