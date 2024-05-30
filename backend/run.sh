#!/bin/bash

if [[ $1 == "--test" ]]; then
    hypercorn main:app --bind 0.0.0.0:8000 --log-level debug --reload
else
    # print the value of the WORKERS environment variable
    echo "WORKERS: ${WORKERS:-1}"
    hypercorn main:app --workers ${WORKERS:-1} --bind 0.0.0.0:8000
fi