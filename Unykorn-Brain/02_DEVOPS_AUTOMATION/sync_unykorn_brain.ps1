# Unykorn Neural Vault Real-Time Mirroring Daemon
$source = "C:\Unykorn-Brain"
$destination = "C:\Users\Kevan\Obsidian-Vault\Unykorn-Brain"

Write-Host "[+] Unykorn Neural Vault Watcher Active..." -ForegroundColor Cyan
Write-Host "    Source:      $source"
Write-Host "    Destination: $destination"

# Initial Mirror Sync
robocopy $source $destination /MIR /FFT /Z /XA:H /W:1 /R:1 | Out-Null
Write-Host "[+] Initial synchronization complete." -ForegroundColor Green

# File System Watcher on Primary Brain Root
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $source
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Change detected: $changeType -> $path" -ForegroundColor Yellow
    
    Start-Sleep -Milliseconds 500
    robocopy $source $destination /MIR /FFT /Z /XA:H /W:1 /R:1 | Out-Null
    Write-Host "[+] Mirrored to Obsidian Vault." -ForegroundColor Green
}

Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Deleted" -Action $action | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null

while ($true) { Start-Sleep -Seconds 1 }
