#!/bin/bash
# Monitor training continuously
while true; do
    clear
    python check_training_progress.py
    echo ""
    echo "Checking again in 60 seconds (Ctrl+C to stop)..."
    sleep 60
done
