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
    echo "  Python 3 is required. Opening setup guide in your browser..."
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open setup.html
    else
        xdg-open setup.html 2>/dev/null || sensible-browser setup.html 2>/dev/null || echo "  Please open setup.html in your browser manually"
    fi
    exit 0
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

# Check if port 3131 is already in use
PORT=3131
if command -v lsof &> /dev/null; then
    if lsof -i :$PORT -sTCP:LISTEN &> /dev/null; then
        echo "  Warning: Port $PORT is already in use."
        echo "  Another instance may be running."
        echo ""
        echo "  To stop the other instance, open it in your browser"
        echo "  and click the power button, or run:"
        echo "    kill \$(lsof -t -i :$PORT)"
        echo ""
        exit 1
    fi
elif command -v ss &> /dev/null; then
    if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
        echo "  Warning: Port $PORT is already in use."
        echo "  Another instance may be running."
        echo ""
        exit 1
    fi
fi

echo "  Workspace: $(pwd)"
echo "  Starting server on http://localhost:3131"
echo "  Press Ctrl+C to stop"
echo ""

# Open browser after a short delay
(sleep 2 && python3 -c "import webbrowser; webbrowser.open('http://localhost:3131')" 2>/dev/null) &

# Start the server
cd app
python3 server.py
