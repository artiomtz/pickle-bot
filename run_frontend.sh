#!/usr/bin/env bash

# Load .env variables
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo ">>> Starting Pickle Bot Discord Frontend..."
echo ">>> Frontend timezone: ${TIMEZONE}"
echo ">>> Backend base URL: ${BACKEND_BASE_URL}"
echo ">>> Polling interval: ${FRONTEND_POLLING_INTERVAL_SECONDS} seconds"

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

# Run Discord frontend
python -m frontend.discord.main
