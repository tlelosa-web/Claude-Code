# SOPS - Sales Order Processing System Launcher
Set-Location -LiteralPath $PSScriptRoot

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

# If a server is already listening on 5000 (e.g. left running from a
# previous launch), don't try to start a second one - just open the browser.
$alreadyRunning = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue

if ($alreadyRunning) {
    Write-Host "Server already running on port 5000 - opening browser only." -ForegroundColor Yellow
} else {
    Write-Host "Launching server at http://127.0.0.1:5000 in a new window..." -ForegroundColor Green
    Start-Process -FilePath "venv\Scripts\python.exe" -ArgumentList "app.py" -WorkingDirectory $PSScriptRoot
    Write-Host "Waiting for it to come up..."
    Start-Sleep -Seconds 3
}

Start-Process "http://127.0.0.1:5000"
