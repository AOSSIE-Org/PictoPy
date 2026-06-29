# =============================================================================
# PictoPy Dev Setup & Launch Script - Windows PowerShell
# Usage: Right-click -> "Run with PowerShell" OR
#        Open PowerShell in PictoPy root and run: .\dev-setup.ps1
# =============================================================================

# Allow script execution if blocked:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

$ErrorActionPreference = "Stop"

# ── Colors / Helpers ──────────────────────────────────────────────────────────
function Ok($msg)     { Write-Host "[OK] $msg" -ForegroundColor Green }
function Skip($msg)   { Write-Host "[SKIP] $msg (already installed, skipping)" -ForegroundColor Cyan }
function Info($msg)   { Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Warn($msg)   { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Fail($msg)   { Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }
function Header($msg) {
    Write-Host ""
    Write-Host "------------------------------------------------" -ForegroundColor Blue
    Write-Host "  $msg" -ForegroundColor White
    Write-Host "------------------------------------------------" -ForegroundColor Blue
}

# ── Validate we are in the PictoPy root ───────────────────────────────────────
$SCRIPT_DIR   = Split-Path -Parent $MyInvocation.MyCommand.Path
$FRONTEND_DIR = Join-Path $SCRIPT_DIR "frontend"
$BACKEND_DIR  = Join-Path $SCRIPT_DIR "backend"
$SYNC_DIR     = Join-Path $SCRIPT_DIR "sync-microservice"

if (-not (Test-Path $FRONTEND_DIR) -or -not (Test-Path $BACKEND_DIR) -or -not (Test-Path $SYNC_DIR)) {
    Fail "Please run this script from the root of the PictoPy repository."
}

# =============================================================================
# PHASE 1 — PREREQUISITES
# =============================================================================
Header "Phase 1: Checking Prerequisites"

# ── Winget (built into Windows 11, available on Win10 too) ───────────────────
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Warn "winget not found. Install 'App Installer' from the Microsoft Store, then re-run."
    Fail "winget is required for auto-installation."
}

# ── Node.js ───────────────────────────────────────────────────────────────────
if (Get-Command node -ErrorAction SilentlyContinue) {
    Skip "Node.js ($(node --version))"
} else {
    Info "Installing Node.js via winget..."
    winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
    # Refresh PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    Ok "Node.js installed ($(node --version))"
}

# ── Rust / Cargo ──────────────────────────────────────────────────────────────
if (Get-Command cargo -ErrorAction SilentlyContinue) {
    Skip "Rust/Cargo ($(cargo --version))"
} else {
    Info "Installing Rust via rustup..."
    winget install -e --id Rustlang.Rustup --accept-source-agreements --accept-package-agreements
    # Refresh PATH
    $env:PATH = "$env:USERPROFILE\.cargo\bin;" + $env:PATH
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        Warn "Rust installed but cargo not in PATH yet."
        Warn "Please restart PowerShell after this script finishes, then re-run."
    } else {
        Ok "Rust installed ($(cargo --version))"
    }
}

# ── Visual Studio C++ Build Tools (required by Tauri on Windows) ──────────────
Info "Checking Visual Studio C++ Build Tools..."
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$hasBuildTools = $false
if (Test-Path $vswhere) {
    $vsInstalls = & $vswhere -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json 2>$null | ConvertFrom-Json
    if ($vsInstalls.Count -gt 0) { $hasBuildTools = $true }
}
if ($hasBuildTools) {
    Skip "Visual Studio C++ Build Tools"
} else {
    Info "Installing Visual Studio Build Tools (this may take a while)..."
    winget install -e --id Microsoft.VisualStudio.2022.BuildTools --accept-source-agreements --accept-package-agreements `
        --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
    Ok "Visual Studio C++ Build Tools installed"
}

# ── WebView2 (required by Tauri on Windows) ───────────────────────────────────
Info "Checking WebView2 Runtime..."
$webview2Key = "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
if (Test-Path $webview2Key) {
    Skip "WebView2 Runtime"
} else {
    Info "Installing WebView2 Runtime..."
    winget install -e --id Microsoft.EdgeWebView2Runtime --accept-source-agreements --accept-package-agreements
    Ok "WebView2 Runtime installed"
}

# ── Miniconda ─────────────────────────────────────────────────────────────────
if (Get-Command conda -ErrorAction SilentlyContinue) {
    Skip "Miniconda/Conda ($(conda --version))"
} else {
    Info "Installing Miniconda..."
    $minicondaUrl = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    $minicondaInstaller = "$env:TEMP\miniconda.exe"
    Invoke-WebRequest -Uri $minicondaUrl -OutFile $minicondaInstaller
    Start-Process -FilePath $minicondaInstaller -ArgumentList "/S /D=$env:USERPROFILE\miniconda3" -Wait
    Remove-Item $minicondaInstaller

    # Add conda to PATH for this session
    $env:PATH = "$env:USERPROFILE\miniconda3\Scripts;" + "$env:USERPROFILE\miniconda3;" + $env:PATH

    if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
        Warn "Miniconda installed but conda not in PATH yet."
        Warn "Please restart PowerShell after this script finishes, then re-run."
        Fail "conda not available in current session."
    }
    Ok "Miniconda installed ($(conda --version))"
}

# Initialize conda for PowerShell if not already done
$condaHook = "$env:USERPROFILE\miniconda3\shell\condabin\conda-hook.ps1"
if (Test-Path $condaHook) {
    & $condaHook
}

# =============================================================================
# PHASE 2 — SERVICE SETUP
# =============================================================================
Header "Phase 2: Setting Up Services"

# ── Frontend ──────────────────────────────────────────────────────────────────
Info "Frontend: checking node_modules..."
if (Test-Path (Join-Path $FRONTEND_DIR "node_modules")) {
    Skip "Frontend npm dependencies"
} else {
    Info "Frontend: running npm install..."
    Push-Location $FRONTEND_DIR
    npm install
    Pop-Location
    Ok "Frontend dependencies installed"
}

# ── Backend ───────────────────────────────────────────────────────────────────
Info "Backend: checking conda environment..."
$BACKEND_ENV = Join-Path $BACKEND_DIR ".env"
if (Test-Path $BACKEND_ENV) {
    Skip "Backend conda environment (.env)"
} else {
    Info "Backend: creating conda environment with Python 3.12..."
    conda create -p $BACKEND_ENV python=3.12 -y
    Ok "Backend conda environment created"
}

Info "Backend: checking Python packages..."
$backendHasFastapi = conda run -p $BACKEND_ENV python -c "import fastapi" 2>$null
if ($LASTEXITCODE -eq 0) {
    Skip "Backend Python packages"
} else {
    Info "Backend: installing Python packages..."
    conda run -p $BACKEND_ENV pip install -r (Join-Path $BACKEND_DIR "requirements.txt")
    Ok "Backend Python packages installed"
}

# ── Sync Microservice ─────────────────────────────────────────────────────────
Info "Sync microservice: checking conda environment..."
$SYNC_ENV = Join-Path $SYNC_DIR ".sync-env"
if (Test-Path $SYNC_ENV) {
    Skip "Sync microservice conda environment (.sync-env)"
} else {
    Info "Sync microservice: creating conda environment with Python 3.12..."
    conda create -p $SYNC_ENV python=3.12 -y
    Ok "Sync microservice conda environment created"
}

Info "Sync microservice: checking Python packages..."
$syncHasFastapi = conda run -p $SYNC_ENV python -c "import fastapi" 2>$null
if ($LASTEXITCODE -eq 0) {
    Skip "Sync microservice Python packages"
} else {
    Info "Sync microservice: installing Python packages..."
    conda run -p $SYNC_ENV pip install -r (Join-Path $SYNC_DIR "requirements.txt")
    Ok "Sync microservice Python packages installed"
}

# =============================================================================
# PHASE 3 — LAUNCH ALL SERVICES
# =============================================================================
Header "Phase 3: Launching All Services"

# Track jobs for cleanup
$jobs = @()

# ── Launch Backend ────────────────────────────────────────────────────────────
Info "Starting backend on port 52123..."
$backendJob = Start-Job -ScriptBlock {
    param($dir, $env)
    Set-Location $dir
    conda run -p $env fastapi dev --port 52123 2>&1 | ForEach-Object { "[BACKEND]   $_" }
} -ArgumentList $BACKEND_DIR, $BACKEND_ENV
$jobs += $backendJob

# ── Launch Sync Microservice ──────────────────────────────────────────────────
Info "Starting sync microservice on port 52124..."
$syncJob = Start-Job -ScriptBlock {
    param($dir, $env)
    Set-Location $dir
    conda run -p $env fastapi dev --port 52124 2>&1 | ForEach-Object { "[SYNC]      $_" }
} -ArgumentList $SYNC_DIR, $SYNC_ENV
$jobs += $syncJob

# ── Launch Frontend ───────────────────────────────────────────────────────────
Info "Starting Tauri frontend..."
$frontendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    npm run tauri dev 2>&1 | ForEach-Object { "[FRONTEND]  $_" }
} -ArgumentList $FRONTEND_DIR
$jobs += $frontendJob

# =============================================================================
# PHASE 4 — HEALTH CHECK + STREAM LOGS
# =============================================================================
Header "Phase 4: Health Check"

Info "Waiting 10 seconds for services to start..."
Start-Sleep -Seconds 10

# Check backend
try {
    Invoke-WebRequest -Uri "http://localhost:52123/docs" -UseBasicParsing -TimeoutSec 3 | Out-Null
    Ok "Backend is running at http://localhost:52123"
} catch {
    Warn "Backend may still be starting up — check [BACKEND] logs below"
}

# Check sync microservice
try {
    Invoke-WebRequest -Uri "http://localhost:52124/docs" -UseBasicParsing -TimeoutSec 3 | Out-Null
    Ok "Sync microservice is running at http://localhost:52124"
} catch {
    Warn "Sync microservice may still be starting — check [SYNC] logs below"
}

Write-Host ""
Write-Host "[OK] PictoPy dev environment is up!" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop all services."
Write-Host ""

# ── Stream logs from all jobs + handle Ctrl+C ────────────────────────────────
try {
    while ($true) {
        foreach ($job in $jobs) {
            $output = Receive-Job -Job $job -ErrorAction SilentlyContinue
            if ($output) {
                foreach ($line in $output) {
                    if ($line -like "\[BACKEND\]*")  { Write-Host $line -ForegroundColor Green }
                    elseif ($line -like "\[SYNC\]*") { Write-Host $line -ForegroundColor Yellow }
                    else                             { Write-Host $line -ForegroundColor Blue }
                }
            }
        }
        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host ""
    Warn "Shutting down all services..."
    foreach ($job in $jobs) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -ErrorAction SilentlyContinue
    }
    Ok "All services stopped. Goodbye!"
}