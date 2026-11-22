#!/usr/bin/env bash
# macOS / Linux setup
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Install Python 3.10+ first"; exit 1; }
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first (brew install ffmpeg / sudo apt install ffmpeg)"; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
mkdir -p secrets
.venv/bin/python -m toonshorts check || true
echo "Setup done. Next: put your keys in secrets/ (see secrets/README.md) and follow the README."
