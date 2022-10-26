param ([Parameter(Mandatory=$true)][int]$rq)
$path = "./rq" + $rq + "_output"
Remove-Item -LiteralPath $path -Force -Recurse
mkdir $path
docker-compose up --build rq$rq