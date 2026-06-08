# SOPS - Sales Order Processing System Launcher
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting SOPS Application..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then: venv\Scripts\pip.exe install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the Flask application
Write-Host "Launching application at http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

& .\venv\Scripts\python.exe app.py

Read-Host "Press Enter to exit"
