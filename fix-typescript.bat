@echo off
echo.
echo ====================================
echo   TypeScript Error Fix Script
echo ====================================
echo.

cd frontend

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

echo.
echo [5/5] Verifying installation...
if exist "node_modules\@radix-ui\react-dropdown-menu" (
    echo     SUCCESS: @radix-ui/react-dropdown-menu is installed!
) else (
    echo     Installing @radix-ui/react-dropdown-menu specifically...
    call npm install @radix-ui/react-dropdown-menu@^2.1.15
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
