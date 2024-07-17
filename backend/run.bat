@echo off

if "%1"=="--test" (
  hypercorn main:app --bind localhost:8000 --log-level debug --reload
) else (
    REM print the value of the WORKERS environment variable
    echo WORKERS: %WORKERS%
    hypercorn main:app --bind localhost:8000 --log-level debug --reload


)
