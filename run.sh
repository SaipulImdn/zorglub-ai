#!/bin/bash

# Zorglub AI - Voice Assistant Runner Script
# Simplifies running the app with proper virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"

echo "Zorglub AI Voice Assistant"
echo "=============================="

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Virtual environment not found!"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if app.py exists
if [ ! -f "$SCRIPT_DIR/app.py" ]; then
    echo "app.py not found!"
    exit 1
fi

cd "$SCRIPT_DIR"

# Parse arguments
if [ $# -eq 0 ]; then
    echo "Starting interactive mode..."
    $VENV_PYTHON app.py
elif [ "$1" = "check" ]; then
    echo "Checking dependencies..."
    $VENV_PYTHON app.py --check
elif [ "$1" = "text" ]; then
    echo "Starting text chat mode..."
    $VENV_PYTHON app.py --text
elif [ "$1" = "voice" ]; then
    echo "Starting voice chat mode..."
    $VENV_PYTHON app.py --voice
elif [ "$1" = "single" ]; then
    echo "Single voice interaction..."
    $VENV_PYTHON app.py --single
elif [ "$1" = "help" ]; then
    echo "Usage: ./run.sh [mode]"
    echo ""
    echo "Modes:"
    echo "  (no args) - Interactive mode with menu"
    echo "  check     - Check dependencies"
    echo "  text      - Text chat mode"
    echo "  voice     - Voice chat mode"
    echo "  single    - Single voice interaction"
    echo "  help      - Show this help"
else
    echo "Unknown mode: $1"
    echo "Use './run.sh help' for available modes"
    exit 1
fi
