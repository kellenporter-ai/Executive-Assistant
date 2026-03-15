@echo off
REM Gemini Executive Assistant — Launcher (Windows)
REM Usage: double-click start.bat

cd /d "%~dp0"
echo.
echo   Gemini Executive Assistant
echo   ==========================
echo.

REM Check Python (the only hard requirement — runs the server)
set PYTHON_CMD=
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
    ) else (
        echo   Python 3 is required. Opening setup guide in your browser...
        start "" "%~dp0setup.html"
        timeout /t 3 /nobreak >nul
        exit /b 0
    )
)

REM Note: Gemini CLI, Node, npm, and git are checked by the web interface.
REM The setup wizard will guide through installing any missing dependencies.

REM Create virtual environment if needed
if not exist "app\.venv" (
    echo   Setting up for the first time...
    %PYTHON_CMD% -m venv app\.venv
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
%PYTHON_CMD% server.py
