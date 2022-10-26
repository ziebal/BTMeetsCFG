Remove-Item -LiteralPath "./output" -Force -Recurse
mkdir output
docker-compose up --build converter