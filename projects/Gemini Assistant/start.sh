#!/usr/bin/env bash
#
# Gemini Executive Assistant — Launcher (macOS/Linux)
#
# Usage: ./start.sh
# First run installs dependencies automatically.
#

set -e

# Navigate to the script's directory (workspace root)
cd "$(dirname "$0")"
WORKSPACE="$(pwd)"

echo ""
echo "  Gemini Executive Assistant"
echo "  =========================="
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "  Error: Python 3 is required but not installed."
    echo "  Install it from https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "app/.venv" ]; then
    echo "  Setting up for the first time..."
    python3 -m venv app/.venv
    echo "  Created virtual environment."
fi

# Activate venv
source app/.venv/bin/activate

# Install dependencies if needed
if [ ! -f "app/.venv/.installed" ]; then
    echo "  Installing dependencies..."
    pip install -q -r app/requirements.txt
    touch app/.venv/.installed
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
