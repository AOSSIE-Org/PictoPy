@echo off
REM Windows batch script for running PictoPy backend

echo Starting backend server...

REM Start the backend server with Hypercorn
cd /d "%~dp0"

if "%1"=="--test" (
    echo Starting Hypercorn server in test environment...
    hypercorn main:app --bind 0.0.0.0:8000 --log-level debug --reload --access-log -
) else (
    REM Print the value of the WORKERS environment variable
    echo WORKERS: %WORKERS%
    if not defined WORKERS (
        hypercorn main:app --workers 1 --bind 0.0.0.0:8000
    ) else (
        hypercorn main:app --workers %WORKERS% --bind 0.0.0.0:8000
    )
)
