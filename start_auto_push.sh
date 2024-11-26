#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

# Start the auto-push script
echo "Starting auto-push script..."
python3 auto_push.py
