# Launches the NamePlate Tool backend + frontend with no visible console
# windows. Invoked via Launch_NamePlate_Tool.vbs (double-click entry point).
# To stop: Stop_NamePlate_Tool.vbs / STOP_PIPELINE.ps1.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root '4_Scripts\backend'
$frontend = Join-Path $root '4_Scripts\frontend'
$log = Join-Path $root '5_Archive_and_Debug\launch_hidden.log'
$pidFile = Join-Path $root '5_Archive_and_Debug\pipeline.pids'

function Write-Log($msg) {
    "$(Get-Date -Format o)  $msg" | Out-File -FilePath $log -Append -Encoding utf8
}

function Show-Message($msg) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($msg, 'NamePlate Tool') | Out-Null
}

$backendPython = Join-Path $backend 'venv\Scripts\python.exe'
if (-not (Test-Path $backendPython)) {
    Write-Log "ERROR: backend venv not found at $backend\venv"
    Show-Message "Backend virtual environment not found.`n`nRun RUN_PIPELINE.bat once from a terminal to set it up, then try this launcher again."
    exit 1
}

Write-Log 'Starting backend (uvicorn, hidden)...'
$backendProc = Start-Process -FilePath $backendPython `
    -ArgumentList '-m', 'uvicorn', 'main:app', '--reload' `
    -WorkingDirectory $backend -WindowStyle Hidden -PassThru

Write-Log 'Starting frontend (vite dev, hidden)...'
$frontendProc = Start-Process -FilePath 'npm.cmd' -ArgumentList 'run', 'dev' `
    -WorkingDirectory $frontend -WindowStyle Hidden -PassThru

# Save the root PIDs so STOP_PIPELINE.ps1 can kill the whole process tree
# under each (uvicorn --reload spawns a worker subprocess; npm spawns a
# cmd.exe -> node.exe chain for vite). A plain port-based kill only hits the
# leaf process and uvicorn's reloader just respawns a new worker.
"$($backendProc.Id)`n$($frontendProc.Id)" | Out-File -FilePath $pidFile -Encoding ascii

Start-Sleep -Seconds 4
Start-Process 'http://localhost:5173'
Write-Log "Launch complete. Backend root PID $($backendProc.Id), frontend root PID $($frontendProc.Id)."
