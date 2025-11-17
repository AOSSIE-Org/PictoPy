# Check if running as Administrator
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This script must be run as Administrator. Please re-run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "Starting Windows setup..." -ForegroundColor Yellow

function Test-Command($command) {
    try { Get-Command $command -ErrorAction Stop; return $true } catch { return $false }
}

function Install-Chocolatey {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# ---- Install Chocolatey if not installed ----
if (-not (Test-Command choco)) {
    Write-Host "Chocolatey is not installed. Installing..." -ForegroundColor Yellow
    Install-Chocolatey
} else {
    Write-Host "Chocolatey is already installed." -ForegroundColor Green
}

# Refresh PATH environment variable
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# ---- Install Visual Studio Build Tools (if not present) ----
Write-Host "Installing Visual Studio Build Tools..." -ForegroundColor Yellow
winget install Microsoft.VisualStudio.2022.BuildTools --force --override "--wait --passive --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows11SDK.22621"

# ---- Check if Visual C++ Build Tools (cl.exe) are available ----
$vsPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC"
if (Test-Path $vsPath) {
    $latestVersion = (Get-ChildItem $vsPath | Sort-Object Name -Descending | Select-Object -First 1).Name
    $clPath = Join-Path -Path $vsPath -ChildPath "$latestVersion\bin\Hostx64\x64\cl.exe"
    
    if (Test-Path $clPath) {
        Write-Host "Visual C++ Build Tools found at: $clPath" -ForegroundColor Green
        # Add to PATH if not already there
        $env:Path = "$vsPath\$latestVersion\bin\Hostx64\x64;$env:Path"
    } else {
        Write-Host "Visual C++ Build Tools (cl.exe) not found." -ForegroundColor Red
        Write-Host "Please open the Visual Studio Installer and ensure the 'Desktop development with C++' workload is installed:" -ForegroundColor Yellow
        Write-Host "   1. Open the Visual Studio Installer." -ForegroundColor Yellow
        Write-Host "   2. Choose 'Modify' on your Visual Studio Build Tools installation." -ForegroundColor Yellow
        Write-Host "   3. Ensure that the 'Desktop development with C++' workload is selected." -ForegroundColor Yellow
    }
} else {
    Write-Host "Visual Studio Build Tools installation path not found." -ForegroundColor Red
    Write-Host "Please open the Visual Studio Installer and ensure the 'Desktop development with C++' workload is installed:" -ForegroundColor Yellow
    Write-Host "   1. Open the Visual Studio Installer." -ForegroundColor Yellow
    Write-Host "   2. Choose 'Modify' on your Visual Studio Build Tools installation." -ForegroundColor Yellow
    Write-Host "   3. Ensure that the 'Desktop development with C++' workload is selected." -ForegroundColor Yellow
}

# ---- Install Rust if not installed ----
if (-not (Test-Command rustc)) {
    Write-Host "Installing Rust..." -ForegroundColor Yellow
    Invoke-WebRequest https://win.rustup.rs/x86_64 -OutFile rustup-init.exe
    .\rustup-init.exe -y
    Remove-Item rustup-init.exe
    
    # Update PATH for Rust
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
} else {
    Write-Host "Rust is already installed. Version: $(rustc --version)" -ForegroundColor Green
}

# ---- Install Node.js if not installed ----
if (-not (Test-Command node)) {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    choco install nodejs-lts -y
    
    # Refresh PATH for Node.js
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
} else {
    Write-Host "Node.js is already installed. Version: $(node --version)" -ForegroundColor Green
}

# ---- Install Python 3.12 directly (without pyenv) ----
if (-not (Test-Command python) -or -not ((python --version 2>&1) -match "3\.12")) {
    Write-Host "Installing Python 3.12..." -ForegroundColor Yellow
    choco install python312 -y
    
    # Refresh PATH for Python
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # Verify Python installation
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "3\.12") {
        Write-Host "Python 3.12 is installed. Version: $pyVersion" -ForegroundColor Green
    } else {
        Write-Host "Failed to install Python 3.12. Please check your installation." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Python 3.12 is already installed. Version: $(python --version)" -ForegroundColor Green
}

# ---- Install CMake if not installed ----
if (-not (Test-Command cmake)) {
    Write-Host "Installing CMake..." -ForegroundColor Yellow
    choco install cmake -y
    
    # Refresh PATH for CMake
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
} else {
    Write-Host "CMake is already installed. Version: $(cmake --version)" -ForegroundColor Green
}

# ---- Set up the frontend ----
Write-Host "Setting up frontend..." -ForegroundColor Yellow
try {
    Set-Location ..\frontend\
    npm install
    
    Set-Location .\src-tauri\
    cargo build
    
    Set-Location ..\..
    Write-Host "Frontend setup completed successfully." -ForegroundColor Green
} catch {
    Write-Host "Error setting up frontend: $_" -ForegroundColor Red
    Set-Location $PSScriptRoot  # Return to original directory
}

# ---- Set up the backend using Python 3.12 ----
Write-Host "Setting up backend..." -ForegroundColor Yellow
try {
    Set-Location .\backend\
    
    # Create virtual environment
    python -m venv .env
    
    # Activate virtual environment and install dependencies
    .\.env\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    deactivate
    
    Set-Location ..
    Write-Host "Backend setup completed successfully." -ForegroundColor Green
} catch {
    Write-Host "Error setting up backend: $_" -ForegroundColor Red
    Set-Location $PSScriptRoot  # Return to original directory
}


# -------------------------
# NODE-BASED pre-commit installer (global hook in package.json)
# Behavior:
#  - if package.json contains "pre-commit" key, we assume the repo uses Node pre-commit.
#  - install local dev deps (idempotent), then run npx pre-commit install
# -------------------------
function Initialize-NodePreCommit {
    param(
        [string]$RepoRoot = $PSScriptRoot
    )

    Write-Host "Checking for Node-based pre-commit in $RepoRoot" -ForegroundColor Yellow
    Push-Location $RepoRoot
    try {
        $pkgJson = Join-Path $RepoRoot "package.json"
        if (-not (Test-Path $pkgJson)) {
            Write-Host "No package.json found — skipping Node pre-commit installation." -ForegroundColor Cyan
            return
        }

        $pkgText = Get-Content -Path $pkgJson -Raw
        if ($pkgText -notmatch '"pre-commit"\s*:') {
            Write-Host 'package.json does not contain a "pre-commit" entry — skipping Node pre-commit install.' -ForegroundColor Cyan
            return
        }

        Write-Host "Detected Node-based pre-commit entry in package.json — installing Node pre-commit and common dev dependencies..." -ForegroundColor Green

        # Install pre-commit itself, and common frontend deps used by hooks (idempotent).
        # Adjust the dependency list to match your repo's actual devDependencies if needed.
        npm --prefix $RepoRoot install --save-dev pre-commit prettier prettier-plugin-tailwindcss --no-audit --no-fund

        # Clear any existing node-based pre-commit caches/hooks (safe no-op)
        try {
            npx --prefix $RepoRoot --no-install pre-commit clear 2>$null
        } catch {
            # ignore
        }

        # Install node-based git hook(s) (creates .git/hooks/pre-commit)
        npx --prefix $RepoRoot --no-install pre-commit install

        Write-Host "Node pre-commit installation finished." -ForegroundColor Green
    } catch {
        Write-Host "Error during Node pre-commit setup: $_" -ForegroundColor Red
    } finally {
        Pop-Location
    }
}

# Run Node pre-commit setup at repo root
Initialize-NodePreCommit -RepoRoot $PSScriptRoot

Write-Host "Windows setup complete!" -ForegroundColor Green
Write-Host "Please restart your computer to ensure all changes take effect." -ForegroundColor Yellow

