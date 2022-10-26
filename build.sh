#!/bin/sh
echo 'Building base image for BTMeetsCFG ...'
docker build -t norm/fuzzer-base-image - < base-image.dockerfile
echo 'Done!'
echo 'You can now run docker-compose up!'