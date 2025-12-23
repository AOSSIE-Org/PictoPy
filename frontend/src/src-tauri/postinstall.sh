#!/bin/bash

# Function to update permissions for a given path pattern
update_permissions() {
  local pattern="$1"
  local path=$(dpkg -L picto-py | grep "$pattern" | head -n 1)
  
  if [ -n "$path" ] && [ -d "$path" ]; then
    chmod -R 777 "$path"
    echo "Permissions for $path have been updated to 777."
  else
    echo "Path not found or is not a directory: $path (pattern: $pattern)"
  fi
}

# Update permissions for both directories
update_permissions "resources/backend"
update_permissions "resources/sync-microservice"
