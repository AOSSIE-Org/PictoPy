# PowerShell script to set up Tauri development environment on Windows

# ANSI escape codes for colors
$RESET = "`e[0m"
$RED = "`e[31m"
$GREEN = "`e[32m"
$YELLOW = "`e[33m"

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
    Write-Output "${YELLOW}Chocolatey is not installed. Installing...${RESET}"
    Install-Chocolatey
} else {
    Write-Output "${GREEN}Chocolatey is already installed.${RESET}"
}

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install Visual Studio Build Tools
if (-not (Test-Path "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools")) {
    Write-Output "${YELLOW}Installing Visual Studio Build Tools...${RESET}"
    choco install visualstudio2019buildtools -y --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
} else {
    Write-Output "${GREEN}Visual Studio Build Tools are already installed.${RESET}"
}

# Install WebView2 Runtime
if (-not (Test-Path "C:\Program Files (x86)\Microsoft\EdgeWebView\Application\msedgewebview2.exe")) {
    Write-Output "${YELLOW}Installing WebView2 Runtime...${RESET}"
    choco install microsoft-edge-webview2-runtime -y
} else {
    Write-Output "${GREEN}WebView2 Runtime is already installed.${RESET}"
}

# Install Rust
if (-not (Test-Command rustc)) {
    Write-Output "${YELLOW}Installing Rust...${RESET}"
    Invoke-WebRequest https://win.rustup.rs/x86_64 -OutFile rustup-init.exe
    .\rustup-init.exe -y
    Remove-Item rustup-init.exe
} else {
    Write-Output "${GREEN}Rust is already installed. Version: $(rustc --version)${RESET}"
}

# Install Node.js
if (-not (Test-Command node)) {
    Write-Output "${YELLOW}Installing Node.js...${RESET}"
    choco install nodejs-lts -y
} else {
    Write-Output "${GREEN}Node.js is already installed. Version: $(node --version)${RESET}"
}

# Install CMake
if (-not (Test-Command cmake)) {
    Write-Output "${YELLOW}Installing CMake...${RESET}"
    choco install cmake -y
} else {
    Write-Output "${GREEN}CMake is already installed. Version: $(cmake --version)${RESET}"
}

# Refresh environment variables again
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Output "${GREEN}All required tools and libraries are installed!${RESET}"
Write-Output "${YELLOW}Please restart your computer to ensure all changes take effect.${RESET}"