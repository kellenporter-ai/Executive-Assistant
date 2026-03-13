@echo off
REM Gemini Executive Assistant — Launcher (Windows)
REM Usage: double-click start.bat

cd /d "%~dp0"
echo.
echo   Gemini Executive Assistant
echo   ==========================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo   Error: Python 3 is required but not installed.
    echo   Install it from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment if needed
if not exist "app\.venv" (
    echo   Setting up for the first time...
    python -m venv app\.venv
    echo   Created virtual environment.
)

REM Activate venv
call app\.venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "app\.venv\.installed" (
    echo   Installing dependencies...
    pip install -q -r app\requirements.txt
    echo. > app\.venv\.installed
    echo   Dependencies installed.
)

echo   Starting server on http://localhost:3131
echo   Press Ctrl+C to stop
echo.

REM Open browser after delay
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:3131"

REM Start the server
cd app
python server.py
