#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the optimized ODS reader
python3 main.py
