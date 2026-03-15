#!/usr/bin/env bash
#
# Gemini Executive Assistant — Launcher (macOS/Linux)
#
# Usage: ./start.sh
# First run installs Python dependencies automatically.
#

set -e

# Navigate to the script's directory (workspace root)
cd "$(dirname "$0")"
WORKSPACE="$(pwd)"

echo ""
echo "  Gemini Executive Assistant"
echo "  =========================="
echo ""

# Check Python 3 (the only hard requirement — runs the server)
if ! command -v python3 &> /dev/null; then
    echo "  Error: Python 3 is required but not installed."
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  macOS:   brew install python3"
    elif [[ -f /etc/debian_version ]]; then
        echo "  Ubuntu/Debian: sudo apt install python3 python3-venv"
    elif [[ -f /etc/fedora-release ]]; then
        echo "  Fedora:  sudo dnf install python3"
    elif [[ -f /etc/arch-release ]]; then
        echo "  Arch:    sudo pacman -S python"
    else
        echo "  Install from: https://www.python.org/downloads/"
    fi
    exit 1
fi

# Note: Gemini CLI, Node, npm, and git are checked by the web interface.
# The setup wizard will guide through installing any missing dependencies.

# Create virtual environment if it doesn't exist
if [ ! -d "app/.venv" ]; then
    echo "  Setting up for the first time..."
    python3 -m venv app/.venv
    echo "  Created virtual environment."
fi

# Activate venv
source app/.venv/bin/activate

# Install/update dependencies if requirements changed
REQS_HASH=$(md5sum app/requirements.txt 2>/dev/null | cut -d' ' -f1 || md5 -q app/requirements.txt 2>/dev/null)
if [ ! -f "app/.venv/.installed" ] || [ "$(cat app/.venv/.installed 2>/dev/null)" != "$REQS_HASH" ]; then
    echo "  Installing dependencies..."
    pip install -q -r app/requirements.txt
    echo "$REQS_HASH" > app/.venv/.installed
    echo "  Dependencies installed."
fi

echo "  Starting server on http://localhost:3131"
echo "  Press Ctrl+C to stop"
echo ""

# Open browser after a short delay
(sleep 2 && python3 -c "import webbrowser; webbrowser.open('http://localhost:3131')" 2>/dev/null) &

# Start the server
cd app
python3 server.py
