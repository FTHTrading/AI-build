# ==============================================================================
# UNYKORN MULTI-DAEMON ORCHESTRATOR & VAULT SUPERVISOR
# Entity: Unykorn LLC | Operator: Kevan Burns (Founder/Owner/CEO)
# ==============================================================================

$source = "C:\Unykorn-Brain"
$destination = "C:\Users\Kevan\Obsidian-Vault\Unykorn-Brain"
$scriptsDir = "C:\Users\Kevan\scripts"
$rustChainDir = "C:\Users\Kevan\AI-build\unykorn-core"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   UNYKORN 24/7 RUNTIME ENGINE & SUPERVISOR             " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Start or Verify FastAPI Command Server (Port 8790)
$apiProc = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*vault_api_server.py*" }
if (-not $apiProc) {
    Write-Host "[+] Launching Vault FastAPI Server on port 8790..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "$scriptsDir\vault_api_server.py" -WindowStyle Hidden
} else {
    $pidNum = $apiProc.ProcessId
    Write-Host "[OK] Vault FastAPI Server active (PID: $pidNum)" -ForegroundColor Green
}

# 2. Start or Verify Genesis402 (x402) A2A Gateway (Port 4020)
$a2aProc = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*unykorn_x402_a2a_daemon.py*" }
if (-not $a2aProc) {
    Write-Host "[+] Launching Genesis402 A2A Gateway on port 4020..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "$scriptsDir\unykorn_x402_a2a_daemon.py" -WindowStyle Hidden
} else {
    $a2aPid = $a2aProc.ProcessId
    Write-Host "[OK] Genesis402 A2A Gateway active (PID: $a2aPid)" -ForegroundColor Green
}

# 3. Initial Vault Synchronization
Write-Host "[*] Executing initial Vault Mirror sync..." -ForegroundColor Cyan
robocopy $source $destination /MIR /FFT /Z /XA:H /W:1 /R:1 | Out-Null
Write-Host "[OK] Initial Vault mirror complete." -ForegroundColor Green

# 4. File System Watcher Daemon Loop
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $source
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    $timeStamp = (Get-Date).ToString("HH:mm:ss")
    Write-Host "[$timeStamp] Vault Event ($changeType): $path" -ForegroundColor DarkGray
    
    Start-Sleep -Milliseconds 500
    robocopy $source $destination /MIR /FFT /Z /XA:H /W:1 /R:1 | Out-Null
}

Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Deleted" -Action $action | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null

Write-Host "[+] All daemons online. Entering supervisory loop..." -ForegroundColor Green
while ($true) { Start-Sleep -Seconds 2 }
