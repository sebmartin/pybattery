#!/bin/bash
set -euo pipefail

# Move to the root of the git repo
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# echo "Running from repo root: $REPO_ROOT"

mkdir venv
pip3 install 
pip3 install rpi-gpio -t venv
pip3 install adafruit-blinka -t venv
