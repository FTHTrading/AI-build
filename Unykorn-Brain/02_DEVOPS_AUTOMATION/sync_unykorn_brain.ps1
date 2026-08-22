# ==============================================================================
# UNYKORN MULTI-DAEMON ORCHESTRATOR & VAULT SUPERVISOR
# Entity: Unykorn LLC | Operator: Kevan Burns (Founder/Owner/CEO)
# ==============================================================================

$source = "C:\Unykorn-Brain"
$destination = "C:\Users\Kevan\Obsidian-Vault\Unykorn-Brain"
$scriptsDir = "C:\Users\Kevan\scripts"
$rustChainDir = "C:\Users\Kevan\AI-build\unykorn-chain"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   UNYKORN 24/7 RUNTIME ENGINE & GENESIS402 GATEWAY     " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Start or Verify FastAPI Command Server (Port 8790)
$apiProc = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*vault_api_server.py*" }
if (-not $apiProc) {
    Write-Host "[+] Launching Vault FastAPI Server on port 8790..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "$scriptsDir\vault_api_server.py" -WindowStyle Hidden
} else {
    Write-Host "[✓] Vault FastAPI Server active (PID: $($apiProc.ProcessId))" -ForegroundColor Green
}

# 2. Start or Verify Rust Layer-1 Node (Port 8791)
$rustProc = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*unykorn-chain*" }
if (-not $rustProc) {
    Write-Host "[+] Launching Rust Layer-1 Consensus Node on port 8791..." -ForegroundColor Yellow
    Start-Process -FilePath "cargo" -ArgumentList "run --manifest-path $rustChainDir\Cargo.toml --release" -WindowStyle Hidden
} else {
    Write-Host "[✓] Rust Layer-1 Node active (PID: $($rustProc.ProcessId))" -ForegroundColor Green
}

# 3. Start or Verify Genesis402 (x402) A2A Gateway (Port 4020)
$a2aProc = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*unykorn_x402_a2a_daemon.py*" }
if (-not $a2aProc) {
    Write-Host "[+] Launching Genesis402 A2A Gateway on port 4020..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "$scriptsDir\unykorn_x402_a2a_daemon.py" -WindowStyle Hidden
} else {
    Write-Host "[✓] Genesis402 A2A Gateway active (PID: $($a2aProc.ProcessId))" -ForegroundColor Green
}

# 4. Initial Vault Synchronization
Write-Host "[*] Executing initial Vault Mirror sync..." -ForegroundColor Cyan
robocopy $source $destination /MIR /FFT /Z /XA:H /W:1 /R:1 | Out-Null
Write-Host "[✓] Initial Vault mirror complete." -ForegroundColor Green

# 5. File System Watcher Daemon Loop
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $source
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Vault Event ($changeType): $path" -ForegroundColor DarkGray
    
    Start-Sleep -Milliseconds 500
    robocopy $source $destination /MIR /FFT /Z /XA:H /W:1 /R:1 | Out-Null
}

Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Deleted" -Action $action | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null

Write-Host "[+] All daemons online. Entering supervisory loop..." -ForegroundColor Green
while ($true) { Start-Sleep -Seconds 2 }
