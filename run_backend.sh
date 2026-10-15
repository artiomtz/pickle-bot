#!/usr/bin/env bash

# Load .env variables
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo ">>> Starting Pickle Bot Backend..."
echo ">>> Dev mode: ${IS_DEV}"
echo ">>> Web enabled: ${WEB_ENABLED}"
echo ">>> Allowed origins: ${ALLOWED_ORIGINS}"

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

# Run FastAPI server
if [ "$IS_DEV" = "true" ]; then
  uvicorn backend.main:app --reload
else
  uvicorn backend.main:app --port 8000
fi
