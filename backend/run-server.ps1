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

# Main Script
if ($args[0] -eq "--test") {
    while ($script:running) {
        Write-Host "Starting Hypercorn server in test environment..."
        
        # Start the Hypercorn server process
        $process = Start-Process -FilePath "hypercorn" `
                                 -ArgumentList "main:app --bind 0.0.0.0:8000 --log-level debug --reload --access-log -" `
                                 -RedirectStandardOutput "hypercorn.log" `
                                 -RedirectStandardError "hypercorn.log" `
                                 -PassThru

        # Monitor the log file for errors
        Get-Content -Path "hypercorn.log" -Wait | ForEach-Object {
            Write-Host $_
            if ($_ -match "Syntax error") {
                Write-Host "Syntax error detected. Restarting server..."
                $process.Kill()
            }
        }

        Write-Host "Hypercorn server crashed in test environment. Restarting in 3 seconds..."
        Start-Sleep -Seconds 3
    }
} else {
    # Model-download and global-reclustering job tracking is in-memory and
    # per-worker, so the server must run with a single worker; a job started in
    # one worker would be invisible to others (missed status polls, duplicate
    # jobs). Do not raise the worker count above 1.

    # Start the Hypercorn server
    $process = Start-Process -FilePath "hypercorn" `
                             -ArgumentList "main:app --workers 1 --bind 0.0.0.0:8000" `
                             -PassThru

    # Wait for process termination or Ctrl+C
    while ($process -and !$process.HasExited -and $script:running) {
        Start-Sleep -Milliseconds 100
    }

    # Cleanup
    if ($process -and !$process.HasExited) {
        $process.Kill()
    }
}

Write-Host "Script has exited."