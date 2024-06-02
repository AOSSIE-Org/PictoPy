@echo off

REM Navigate to the backend directory
cd ..
cd backend
echo Starting backend server...
start "" /B run.bat
cd ..

REM Wait for a moment before starting the frontend
timeout /t 5

REM Navigate to the frontend directory
cd frontend
echo Starting frontend server...
npm run tauri dev
