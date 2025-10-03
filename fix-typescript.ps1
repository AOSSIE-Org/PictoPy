# Type# Save current location
$rootPath = Get-Location

# Navigate to frontend directory
Write-Host "📁 Navigating to frontend directory..." -ForegroundColor Yellow

if (-not (Test-Path "frontend")) {
    Write-Host ""
    Write-Host "❌ ERROR: Directory 'frontend' not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

try {
    Set-Location -Path "frontend" -ErrorAction Stop
    Write-Host "✅ Changed to frontend directory" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ ERROR: Failed to change to 'frontend' directory!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Clear TypeScript cache
Write-Host "🧹 Clearing TypeScript cache..." -ForegroundColor Yellowror Fix Script for Windows
# This script will reinstall node_modules and fix the Radix UI error

Write-Host "🔧 Comprehensive TypeScript Error Fix..." -ForegroundColor Cyan
Write-Host ""

# Save current location
$rootPath = Get-Location

# Navigate to frontend directory
Write-Host "📁 Navigating to frontend directory..." -ForegroundColor Yellow
Set-Location -Path "frontend"

# Clear TypeScript cache
Write-Host "�️  Clearing TypeScript cache..." -ForegroundColor Yellow
$tsCachePath = Join-Path $env:TEMP "typescript"
if (Test-Path $tsCachePath) {
    Remove-Item -Recurse -Force $tsCachePath -ErrorAction SilentlyContinue
    Write-Host "✅ Cleared TypeScript cache" -ForegroundColor Green
}

# Remove node_modules
Write-Host "📦 Removing old node_modules..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Remove-Item -Recurse -Force "node_modules"
    Write-Host "✅ Removed node_modules" -ForegroundColor Green
}

# Remove lock files
if (Test-Path "package-lock.json") {
    Remove-Item -Force "package-lock.json"
    Write-Host "✅ Removed package-lock.json" -ForegroundColor Green
}

if (Test-Path "yarn.lock") {
    Remove-Item -Force "yarn.lock"
    Write-Host "✅ Removed yarn.lock" -ForegroundColor Green
}

Write-Host ""
Write-Host "📥 Installing dependencies (this may take 3-5 minutes)..." -ForegroundColor Yellow
Write-Host "    Please be patient..." -ForegroundColor Gray

# Clean npm cache first
npm cache clean --force | Out-Null

# Install dependencies
$installResult = npm install 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Error installing dependencies" -ForegroundColor Red
    Write-Host $installResult -ForegroundColor Red
    Set-Location $rootPath
    exit 1
}

# Verify @radix-ui/react-dropdown-menu is installed
Write-Host ""
Write-Host "🔍 Verifying @radix-ui/react-dropdown-menu installation..." -ForegroundColor Yellow
$radixPath = "node_modules\@radix-ui\react-dropdown-menu"
if (Test-Path $radixPath) {
    Write-Host "✅ @radix-ui/react-dropdown-menu found!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Package not found, installing specifically..." -ForegroundColor Yellow
    # Pin to ^2.1.15 for React 19 compatibility (current as of Oct 2025)
    # Check for updates: https://www.npmjs.com/package/@radix-ui/react-dropdown-menu
    # Revisit when upgrading to React 20 or if type issues persist
    npm install @radix-ui/react-dropdown-menu@^2.1.15
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ ERROR: Failed to install @radix-ui/react-dropdown-menu!" -ForegroundColor Red
        Write-Host "Please check your internet connection and try again." -ForegroundColor Yellow
        Write-Host ""
        Set-Location $rootPath
        exit 1
    }
    
    Write-Host "✅ @radix-ui/react-dropdown-menu installed successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ All dependencies are now properly installed!" -ForegroundColor Green
Write-Host ""
Write-Host "🔄 IMPORTANT - Final Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Close VS Code completely (File → Exit)" -ForegroundColor White
Write-Host "2. Reopen VS Code" -ForegroundColor White
Write-Host "3. Open the PictoPy project" -ForegroundColor White
Write-Host "4. Wait 20-30 seconds for TypeScript to index" -ForegroundColor White
Write-Host ""
Write-Host "OR (if you prefer not to restart VS Code):" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Press Ctrl+Shift+P" -ForegroundColor White
Write-Host "2. Type 'Developer: Reload Window'" -ForegroundColor White
Write-Host "3. Press Enter" -ForegroundColor White
Write-Host ""
Write-Host "✨ Done! Your TypeScript errors should be resolved." -ForegroundColor Green

Set-Location $rootPath
