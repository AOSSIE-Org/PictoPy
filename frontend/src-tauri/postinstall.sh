#!/bin/bash

# Get the first path matching "resources/server" from dpkg -L picto-py output
SERVER_PATH=$(dpkg -L picto-py | grep "resources/server" | head -n 1)
# Check if the path exists
if [ -n "$SERVER_PATH" ] && [ -d "$SERVER_PATH" ]; then
  # Change permissions to allow read, write, and execute for all users
  chmod -R 777 "$SERVER_PATH"
  echo "Permissions for $SERVER_PATH have been updated to 777."
else
  echo "Path not found or is not a directory: $SERVER_PATH"
fi
