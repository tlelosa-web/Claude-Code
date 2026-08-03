# Stops the NamePlate Tool. Primary method: kill the root backend/frontend
# process trees recorded by RUN_PIPELINE_HIDDEN.ps1 (taskkill /T kills a
# process and everything it spawned in one shot -- this matters because
# uvicorn --reload runs a supervisor that respawns its worker if only the
# worker is killed, and npm's `run dev` spawns a cmd.exe -> node.exe chain).
# Fallback: sweep whatever is still listening on 8000/5173, in case the pid
# file is stale or missing.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root '5_Archive_and_Debug\pipeline.pids'

function Show-Message($msg) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($msg, 'NamePlate Tool') | Out-Null
}

$killedAny = $false

if (Test-Path $pidFile) {
    $trackedPids = Get-Content $pidFile | Where-Object { $_ -match '^\d+$' }
    foreach ($trackedPid in $trackedPids) {
        if (Get-Process -Id $trackedPid -ErrorAction SilentlyContinue) {
            taskkill /PID $trackedPid /T /F | Out-Null
            $killedAny = $true
        }
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 1

# Fallback sweep for anything the pid file didn't cover.
$ports = 8000, 5173
$strayPids = @()
foreach ($p in $ports) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction Stop
        $strayPids += $conns.OwningProcess
    } catch {
        # nothing listening on this port
    }
}
$strayPids = $strayPids | Sort-Object -Unique
foreach ($strayPid in $strayPids) {
    try {
        taskkill /PID $strayPid /T /F | Out-Null
        $killedAny = $true
    } catch {
        # already gone
    }
}

if ($killedAny) {
    Show-Message 'NamePlate Tool stopped.'
} else {
    Show-Message "NamePlate Tool doesn't appear to be running (nothing tracked, nothing listening on ports 8000 or 5173)."
}
