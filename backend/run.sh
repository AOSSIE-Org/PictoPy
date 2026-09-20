#!/bin/bash

trap ctrl_c INT

function ctrl_c() {
    echo "Exiting..."
    exit 0
}

if [[ $1 == "--test" ]]; then
    while true; do
        echo "Starting Hypercorn server in test environment..."
        hypercorn main:app --bind 0.0.0.0:8000 --log-level debug --reload --access-log - 2>&1 | while IFS= read -r line; do
            echo "$line"
            if echo "$line" | grep -q "Syntax error"; then
                echo "Syntax error detected. Restarting server..."
            fi
        done
        
        echo "Hypercorn server crashed in test environment. Restarting in 3 seconds..."
        sleep 3
    done
else
    # Model-download and reclustering jobs are tracked in memory, per worker, so
    # a second worker would answer status polls it knows nothing about.
    hypercorn main:app --workers 1 --bind 0.0.0.0:8000
fi