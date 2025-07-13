#!/bin/bash
# Run Zorglub AI with different models
# Usage: ./run_with_model.sh [model] [mode]
# Example: ./run_with_model.sh mistral --text
#          ./run_with_model.sh deepseek-r1 --voice

MODEL=${1:-mistral}
MODE=${2:-}

echo "🚀 Starting Zorglub AI with model: $MODEL"

# Activate virtual environment
source venv/bin/activate

# Set model and run
OLLAMA_MODEL=$MODEL python app.py $MODE
