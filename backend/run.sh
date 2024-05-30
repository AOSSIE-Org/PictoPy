#!/bin/bash

if [[ $1 == "--test" ]]; then
    uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug --reload
else
    # print the value of the WORKERS environment variable
    echo "WORKERS: ${WORKERS:-1}"
    gunicorn main:app --workers=${WORKERS:-1} -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --preload
fi