#!/bin/bash

set -e

APP_FILE="main.py"
REQUIREMENTS_FILE="requirements.txt"
VENV_DIR="venv"

# Create a virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install requirements
echo "Installing dependencies from $REQUIREMENTS_FILE..."
pip install -r "$REQUIREMENTS_FILE"

echo "Starting the $APP_FILE..."
python "$APP_FILE"
