#!/bin/bash

if [ -z "$1" ]
then
    echo "USAGE: ./ingest.sh {file}"
    exit
fi

FILE=$1
FILENAME=${FILE%.*}
QUEUE=$(date +%Y%m%d%H%M%S).txt

cp $FILE /mnt/volume1/Bagit/Tgz
echo $FILENAME > /mnt/volume1/Bagit/Coda/$(date +%Y%m%d%H%M%S).txt

echo "QUEUE: " $QUEUE
