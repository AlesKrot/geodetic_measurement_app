#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -d "$PROJECT_ROOT/.venv" ]; then
  echo "Virtual environment not found at $PROJECT_ROOT/.venv"
  echo "Create it first: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install -e ."
  exit 1
fi

. "$PROJECT_ROOT/.venv/bin/activate"
export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python -m geodetic_app
