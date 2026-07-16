@echo off
title SOPS Launcher
cd /d "%~dp0"

echo ========================================
echo Starting SOPS Application...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

REM If a server is already listening on 5000 (e.g. left running from a
REM previous launch), don't try to start a second one - just open the browser.
netstat -ano | findstr /r ":5000 .*LISTENING" >nul
if %errorlevel%==0 (
    echo Server already running on port 5000 - opening browser only.
) else (
    echo Launching server at http://127.0.0.1:5000 in a new window...
    start "SOPS Server" cmd /k "cd /d "%~dp0" && venv\Scripts\python.exe app.py"
    echo Waiting for it to come up...
    timeout /t 3 /nobreak >nul
)

start "" "http://127.0.0.1:5000"
exit /b 0
