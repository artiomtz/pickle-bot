#!/usr/bin/env bash

# Load .env variables
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo ">>> Running Pickle Bot backend tests..."
echo ">>> Dev mode: ${IS_DEV}"

# Activate virtual environment
if [ -d ".venv" ]; then
  echo ">>> Activating virtual environment..."

  if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate

  elif [ -f ".venv-wsl/bin/activate" ]; then
    source .venv-wsl/bin/activate

  elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate

  else
    echo ">>> WARNING: No activate script found"
  fi
fi

pytest backend/tests -s
