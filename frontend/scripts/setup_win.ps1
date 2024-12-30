# PowerShell script to set up Tauri development environment on Windows

# Function to check if a command exists
function Test-Command($command) {
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try { if (Get-Command $command) { return $true } }
    catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
}

# Function to install Chocolatey
function Install-Chocolatey {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Check and install Chocolatey
if (-not (Test-Command choco)) {
    Write-Host "Chocolatey is not installed. Installing..." -ForegroundColor Yellow
    Install-Chocolatey
} else {
    Write-Host "Chocolatey is already installed." -ForegroundColor Green
}

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install Visual Studio Build Tools
if (-not (Test-Path "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools")) {
    Write-Host "Installing Visual Studio Build Tools..." -ForegroundColor Yellow
    choco install visualstudio2019buildtools -y --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
} else {
    Write-Host "Visual Studio Build Tools are already installed." -ForegroundColor Green
}

# Install WebView2 Runtime
if (-not (Test-Path "C:\Program Files (x86)\Microsoft\EdgeWebView\Application\msedgewebview2.exe")) {
    Write-Host "Installing WebView2 Runtime..." -ForegroundColor Yellow
    choco install microsoft-edge-webview2-runtime -y
} else {
    Write-Host "WebView2 Runtime is already installed." -ForegroundColor Green
}

# Install Rust
if (-not (Test-Command rustc)) {
    Write-Host "Installing Rust..." -ForegroundColor Yellow
    Invoke-WebRequest https://win.rustup.rs/x86_64 -OutFile rustup-init.exe
    .\rustup-init.exe -y
    Remove-Item rustup-init.exe
} else {
    Write-Host "Rust is already installed. Version: $(rustc --version)" -ForegroundColor Green
}

# Install Node.js
if (-not (Test-Command node)) {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    choco install nodejs-lts -y
} else {
    Write-Host "Node.js is already installed. Version: $(node --version)" -ForegroundColor Green
}

# Install CMake
if (-not (Test-Command cmake)) {
    Write-Host "Installing CMake..." -ForegroundColor Yellow
    choco install cmake -y
} else {
    Write-Host "CMake is already installed. Version: $(cmake --version)" -ForegroundColor Green
}

# Refresh environment variables again
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "All required tools and libraries are installed!" -ForegroundColor Green
Write-Host "Please restart your computer to ensure all changes take effect." -ForegroundColor Yellow