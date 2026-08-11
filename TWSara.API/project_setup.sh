#!/usr/bin/env bash
set -euo pipefail   # stop on any error, unset var, or failed pipe

# System deps (apt is idempotent, safe to re-run)
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create venv only if it doesn't already exist
if [ ! -d ".app-env" ]; then
    python3 -m venv .app-env
fi

# Activate for THIS script's remaining steps
source .app-env/bin/activate

# Install deps (guard against missing file)
if [ -f requirements.txt ]; then
    python -m pip install -r requirements.txt
else
    echo "No requirements.txt found — skipping install."
fi
    
# python -m pip freeze > requirements.txt

VENV_PY="$PWD/.app-env/bin/python"

cat <<'EOF'

Setup done.
To use the environment in your terminal, run:
    source .app-env/bin/activate

To run the Flask app with the virtualenv Python without activating:
    "$VENV_PY" app.py
EOF