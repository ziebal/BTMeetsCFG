Write-Host 'Building base image for BTMeetsCFG ...'
Get-Content base-image.dockerfile | docker build -t norm/fuzzer-base-image -
Write-Host 'Done!'
Write-Host 'You can now run docker-compose up!'