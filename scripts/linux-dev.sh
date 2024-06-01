#!/bin/bash

# Function to start the backend server
start_backend() {
  echo "Starting backend server..."
  # Navigate to the backend directory if needed
  

  cd backend || exit
  # Start the backend server
  ./run.sh &

  # Capture the backend server process ID
  BACKEND_PID=$!
  echo "Backend server started with PID: $BACKEND_PID"
}

# Function to start the Tauri app
start_tauri() {
  echo "Starting Tauri app..."
  # Navigate to the Tauri app directory if needed
  cd ..
  cd frontend || exit
  # Start the Tauri app
  
  npm run tauri dev &

  # Capture the Tauri app process ID
  TAURI_PID=$!
  echo "Tauri app started with PID: $TAURI_PID"
}

# Function to stop both processes
stop_apps() {
  echo "Stopping Tauri app..."
  kill "$TAURI_PID"
  echo "Tauri app stopped."

  echo "Stopping backend server..."
  kill "$BACKEND_PID"
  echo "Backend server stopped."
}

# Trap to catch script termination and stop apps
trap stop_apps EXIT

# Start the backend server
start_backend

# Start the Tauri app
start_tauri

# Wait for both processes to finish
wait "$BACKEND_PID" "$TAURI_PID"
