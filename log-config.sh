#!/usr/bin/env bash

LOG_LEVEL_ALL
today=$(date +%Y_%m_%d)
curDir=$(pwd)
logFile=$curDir/log${today}.txt
B_LOG --file $logFile