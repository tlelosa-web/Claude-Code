@echo off
setlocal enabledelayedexpansion
echo === RUN_PIPELINE: Starting NamePlate Tool workflow ===

if not exist "4_Scripts\backend\venv\Scripts\activate.bat" (
  echo Backend virtual environment not found.
  echo Run the following from the project root:
  echo   python -m venv 4_Scripts\backend\venv
  echo   call 4_Scripts\backend\venv\Scripts\activate.bat
  echo   pip install -r 4_Scripts\backend\requirements.txt
  goto end
)

echo Launching backend server...
start "Backend" cmd /k "cd /d %~dp0\4_Scripts\backend && call venv\Scripts\activate.bat && python -m uvicorn main:app --reload"

echo Launching frontend server...
start "Frontend" cmd /k "cd /d %~dp0\4_Scripts\frontend && npm run dev"

:end
