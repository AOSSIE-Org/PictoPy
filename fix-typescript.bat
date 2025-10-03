@echo off
echo.
echo ====================================
echo   TypeScript Error Fix Script
echo ====================================
echo.

if not exist frontend (
    echo ERROR: Directory 'frontend' not found!
    echo Please run this script from the project root directory.
    echo.
    pause
    exit /b 1
)

cd frontend
if errorlevel 1 (
    echo ERROR: Failed to change to 'frontend' directory!
    echo.
    pause
    exit /b 1
)

echo [1/5] Removing node_modules...
if exist node_modules (
    rmdir /s /q node_modules
    echo     Done!
) else (
    echo     Already clean
)

echo.
echo [2/5] Removing package-lock.json...
if exist package-lock.json (
    del /f package-lock.json
    echo     Done!
) else (
    echo     Already clean
)

echo.
echo [3/5] Cleaning npm cache...
call npm cache clean --force
echo     Done!

echo.
echo [4/5] Installing dependencies (this will take 3-5 minutes)...
echo     Please be patient...
call npm install
if errorlevel 1 (
    echo.
    echo ERROR: npm install failed!
    echo Please check your internet connection and try again.
    echo If the problem persists, try running: npm cache clean --force
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [5/5] Verifying installation...
if exist "node_modules\@radix-ui\react-dropdown-menu" (
    echo     SUCCESS: @radix-ui/react-dropdown-menu is installed!
) else (
    echo     Installing @radix-ui/react-dropdown-menu specifically...
    REM Pin to ^2.1.15 for React 19 compatibility (current as of Oct 2025)
    REM Check for updates: https://www.npmjs.com/package/@radix-ui/react-dropdown-menu
    REM Revisit when upgrading to React 20 or if type issues persist
    call npm install @radix-ui/react-dropdown-menu@^2.1.15
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install @radix-ui/react-dropdown-menu!
        echo Please check your internet connection and try again.
        echo.
        pause
        exit /b %ERRORLEVEL%
    )
)

echo.
echo ====================================
echo   Installation Complete!
echo ====================================
echo.
echo IMPORTANT NEXT STEPS:
echo.
echo Option 1 (Recommended):
echo   1. Close VS Code completely
echo   2. Reopen VS Code
echo   3. Wait 30 seconds for TypeScript to index
echo.
echo Option 2 (Faster):
echo   1. In VS Code, press Ctrl+Shift+P
echo   2. Type: Developer: Reload Window
echo   3. Press Enter
echo.
echo The TypeScript error should now be resolved!
echo.
pause
