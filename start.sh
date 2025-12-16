#!/bin/bash

# Install FFmpeg if not present (for non-Docker deployments)
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing FFmpeg..."
    apt-get update && apt-get install -y ffmpeg
fi

# Install Python dependencies
pip install -r requirements.txt --no-cache-dir

# Run the bot
python3 main.py
