# Set up the global flag for running
$script:running = $true
$process = $null  # Variable to store the Hypercorn process

# Function to handle Ctrl+C gracefully
function Handle-CtrlC {
    Write-Host "Exiting gracefully..."
    $script:running = $false

    # Terminate the Hypercorn process if it exists
    if ($process -ne $null -and !$process.HasExited) {
        Write-Host "Terminating Hypercorn process..."
        $process.Kill()
    }
}

# Register an event handler for the Ctrl+C (ConsoleBreak) signal
Register-EngineEvent -SourceIdentifier ConsoleBreak -Action {
    Handle-CtrlC
} | Out-Null

# Check if Hypercorn is installed
try {
    $null = Get-Command hypercorn -ErrorAction Stop
} catch {
    Write-Host "Error: Hypercorn is not installed. Please install it using: pip install hypercorn" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Main Script
try {
    if ($args[0] -eq "--test") {
        while ($script:running) {
            Write-Host "Starting Hypercorn server in test environment..." -ForegroundColor Green
            
            # Start the Hypercorn server process
            $process = Start-Process -FilePath "hypercorn" `
                                   -ArgumentList "main:app --bind 0.0.0.0:8000 --log-level debug --reload --access-log -" `
                                   -RedirectStandardOutput "hypercorn.log" `
                                   -RedirectStandardError "hypercorn.log" `
                                   -PassThru -NoNewWindow

            # Monitor the log file for errors
            Get-Content -Path "hypercorn.log" -Wait | ForEach-Object {
                Write-Host $_
                if ($_ -match "Syntax error") {
                    Write-Host "Syntax error detected. Restarting server..." -ForegroundColor Red
                    $process.Kill()
                }
            }

            Write-Host "Hypercorn server crashed in test environment. Restarting in 3 seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds 3
        }
    } else {
        # Get the WORKERS environment variable or use a default value
        $workers = if ($env:WORKERS) { $env:WORKERS } else { "1" }
        Write-Host "Starting Hypercorn server with $workers workers..." -ForegroundColor Green

        # Start the Hypercorn server
        $process = Start-Process -FilePath "hypercorn" `
                               -ArgumentList "main:app --workers $workers --bind 0.0.0.0:8000" `
                               -PassThru -NoNewWindow

        # Wait for process termination or Ctrl+C
        while ($process -and !$process.HasExited -and $script:running) {
            Start-Sleep -Milliseconds 100
        }
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} finally {
    # Cleanup
    if ($process -and !$process.HasExited) {
        $process.Kill()
    }
    Write-Host "Script has exited." -ForegroundColor Yellow
    Write-Host "Press any key to close..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Write-Host "Script has exited."
