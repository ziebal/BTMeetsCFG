echo "ENV: $ENV"

if [ "$ENV" = "converter" ]; then
    echo "Running converter."
    python3 -m BTMeetsCFG
else
    echo "Running tests."
    echo "RQ: $RQ"
    python3 -m BTMeetsCFG --rq "$RQ"
    cd /source/output/
    echo -e '\e]8;;http://127.0.0.1:9000result.html\aCheck Result: http://127.0.0.1:9000/result.html\e]8;;\a'
    echo -e "To stop the container press CTRL+C"
    python3 -m http.server 9000
fi
