# ==============================================================================
# UNYKORN ENTERPRISE CONTROL ROOM & DONK RUNTIME LAUNCHER
# Executive: Kevan Burns | Entity: Unykorn LLC
# ==============================================================================

param (
    [switch]$SkipBuild = $false,
    [switch]$DockerMode = $false
)

Clear-Host
$Host.UI.RawUI.WindowTitle = "DONK CONTROL ROOM // UNYKORN RUNTIME"

Write-Host "======================================================================" -ForegroundColor DarkRed
Write-Host "         DONK AUTONOMOUS RUNTIME & COGNITIVE CONTROL STATION          " -ForegroundColor Red
Write-Host "                Unykorn LLC - RTX 5090 Engine Active                  " -ForegroundColor DarkGray
Write-Host "======================================================================" -ForegroundColor DarkRed

$workspaceRoot = "C:\Users\Kevan\AI-build"
$brainRoot     = "C:\Unykorn-Brain"
$obsidianRoot  = "C:\Users\Kevan\Obsidian-Vault\Unykorn-Brain"

# 1. Environment & Hardware Diagnostics
Write-Host "`n[1/5] Checking Hardware Engine and Toolchain..." -ForegroundColor Cyan

# Check NVIDIA GPU / CUDA
try {
    $gpuName = (nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>$null)[0]
    if ($gpuName) {
        Write-Host "  [OK] GPU Detected: $gpuName" -ForegroundColor Green
    } else {
        Write-Host "  [!] NVIDIA GPU compute ready." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [!] NVIDIA SMI not responding. Defaulting to system compute." -ForegroundColor Yellow
}

# Check Cargo / Rust
$userProfile = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
$cargoPath = Join-Path $userProfile ".cargo\bin\cargo.exe"
$cargoDir  = Join-Path $userProfile ".cargo\bin"

if (Test-Path $cargoPath) {
    if ($env:Path -notlike "*$cargoDir*") {
        $env:Path = "$env:Path;$cargoDir"
    }
    Write-Host "  [OK] Rust Toolchain: Available ($cargoPath)" -ForegroundColor Green
} else {
    Write-Host "  [!] Cargo not detected in user profile path." -ForegroundColor Yellow
}

# 2. Vault Synchronization
Write-Host "`n[2/5] Synchronizing Neural Vault and Obsidian Mirrors..." -ForegroundColor Cyan
if (Test-Path $brainRoot) {
    robocopy $brainRoot $obsidianRoot /MIR /FFT /Z /XA:H /W:1 /R:1 /NFL /NDL | Out-Null
    Write-Host "  [OK] Mirrored $brainRoot -> $obsidianRoot" -ForegroundColor Green
} else {
    Write-Host "  [!] Unykorn-Brain root path not found." -ForegroundColor Yellow
}

# 3. Microservice Orchestration
Write-Host "`n[3/5] Starting Backend Daemons and IPC Bridges..." -ForegroundColor Cyan

if ($DockerMode) {
    Write-Host "  [*] Launching full stack via Docker Compose..." -ForegroundColor Yellow
    Set-Location $workspaceRoot
    docker compose up -d
} else {
    # A. FastAPI Gateway (Port 8790)
    $apiProc = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*vault_api_server.py*" }
    if (-not $apiProc) {
        Write-Host "  [*] Launching FastAPI Gateway on port 8790..." -ForegroundColor DarkGray
        Start-Process python -ArgumentList "$workspaceRoot\scripts\vault_api_server.py" -WindowStyle Hidden
    } else {
        $pidNum = $apiProc.ProcessId
        Write-Host "  [OK] FastAPI Gateway already running (PID: $pidNum)" -ForegroundColor Green
    }

    # B. Genesis402 Gateway (Port 4020)
    $x402Proc = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*unykorn_x402_a2a_daemon.py*" }
    if (-not $x402Proc) {
        Write-Host "  [*] Launching Genesis402 A2A Gateway on port 4020..." -ForegroundColor DarkGray
        Start-Process python -ArgumentList "$workspaceRoot\scripts\unykorn_x402_a2a_daemon.py" -WindowStyle Hidden
    } else {
        $x402Pid = $x402Proc.ProcessId
        Write-Host "  [OK] Genesis402 Gateway already running (PID: $x402Pid)" -ForegroundColor Green
    }

    # C. Next.js 15 UI (Port 3001)
    $uiProc = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*next*3001*" }
    if (-not $uiProc) {
        Write-Host "  [*] Launching Next.js UI on port 3001..." -ForegroundColor DarkGray
        Start-Process npm -ArgumentList "run dev -- -p 3001" -WorkingDirectory "$workspaceRoot\donk-chat-ui" -WindowStyle Hidden
    } else {
        Write-Host "  [OK] Donk UI already active on port 3001" -ForegroundColor Green
    }
}

Start-Sleep -Seconds 2

# 4. Service Health Grid
Write-Host "`n[4/5] Running Service Diagnostics..." -ForegroundColor Cyan
$endpoints = @(
    @{ Name = "Donk Control UI";  Url = "http://127.0.0.1:3001" },
    @{ Name = "FastAPI Gateway";  Url = "http://127.0.0.1:8790/health" },
    @{ Name = "Rust L1 Node IPC"; Url = "http://127.0.0.1:8791/health" },
    @{ Name = "Genesis402 A2A";   Url = "http://127.0.0.1:4020/x402/health" }
)

foreach ($ep in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $ep.Url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        $code = $response.StatusCode
        Write-Host "  [ONLINE] $($ep.Name) -> $($ep.Url) ($code)" -ForegroundColor Green
    } catch {
        Write-Host "  [OFFLINE/WAITING] $($ep.Name) -> $($ep.Url)" -ForegroundColor DarkYellow
    }
}

# 5. Interactive Control Prompt
Write-Host "`n[5/5] Donk Runtime Operational." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor DarkRed
Write-Host "  [1] Open Donk Control Room in Browser (http://localhost:3001)" -ForegroundColor White
Write-Host "  [2] Run Rust unykorn-core Test Matrix" -ForegroundColor White
Write-Host "  [3] Send Direct CLI Message to Donk" -ForegroundColor White
Write-Host "  [4] Tail Container / Gateway Logs" -ForegroundColor White
Write-Host "  [Q] Exit to Shell" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor DarkRed

while ($true) {
    $choice = Read-Host "`nDONK-CLI"
    switch ($choice) {
        "1" {
            Start-Process "http://localhost:3001"
        }
        "2" {
            Set-Location "$workspaceRoot\unykorn-core"
            if (Test-Path $cargoPath) {
                & $cargoPath test --workspace -- --nocapture
            } else {
                cargo test --workspace -- --nocapture
            }
        }
        "3" {
            $msg = Read-Host "Prompt for Donk"
            if ($msg) {
                $body = @{ message = $msg; workspace = "Unykorn-Core" } | ConvertTo-Json
                try {
                    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8790/v1/chat/threads/master/messages" -Method Post -Body $body -ContentType "application/json"
                    Write-Host "`nDonk Response:" -ForegroundColor Green
                    Write-Host ($res | ConvertTo-Json -Depth 4) -ForegroundColor White
                } catch {
                    Write-Host "Request failed: $_" -ForegroundColor Red
                }
            }
        }
        "4" {
            Set-Location $workspaceRoot
            docker compose logs -f
        }
        "Q" {
            Write-Host "Exiting Donk CLI. Daemons remain running." -ForegroundColor DarkGray
            return
        }
    }
}