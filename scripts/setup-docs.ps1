# PictoPy Documentation Setup Script for Windows
# This script installs the necessary dependencies for building and serving the documentation

Write-Host "📚 Setting up PictoPy Documentation..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH. Please install Python 3 first." -ForegroundColor Red
    exit 1
}

# Check if pip is installed
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip is not installed. Please install pip first." -ForegroundColor Red
    exit 1
}

Write-Host "🐍 Installing documentation dependencies..." -ForegroundColor Yellow

# Install documentation dependencies
if (Test-Path "docs/requirements.txt") {
    Write-Host "📦 Installing from docs/requirements.txt..." -ForegroundColor Cyan
    pip install -r docs/requirements.txt
} elseif (Test-Path "requirements.txt") {
    Write-Host "📦 Installing from requirements.txt..." -ForegroundColor Cyan
    pip install -r requirements.txt
} else {
    Write-Host "❌ No requirements.txt file found. Installing mkdocs-material directly..." -ForegroundColor Yellow
    pip install mkdocs-material
}

# Check if installation was successful
try {
    $mkdocsVersion = mkdocs --version 2>&1
    Write-Host "✅ Documentation dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 You can now:" -ForegroundColor Cyan
    Write-Host "   - Build documentation: mkdocs build" -ForegroundColor White
    Write-Host "   - Serve documentation: mkdocs serve" -ForegroundColor White
    Write-Host "   - Access docs at: http://127.0.0.1:8000/" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 For more information, see the documentation setup guide." -ForegroundColor Cyan
} catch {
    Write-Host "❌ Installation failed. Please check the error messages above." -ForegroundColor Red
    exit 1
} 