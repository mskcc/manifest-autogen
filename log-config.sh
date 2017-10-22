#!/usr/bin/env bash

LOG_LEVEL_ALL
today=$(date +%Y_%m_%d)
logFile=$(dirname $0)/logs/manifest-autogen${today}.log
B_LOG --file $logFile
