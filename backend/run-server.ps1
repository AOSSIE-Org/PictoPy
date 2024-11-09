# PowerShell equivalent of the bash script

# Handle Ctrl+C
$script:running = $true
[Console]::TreatControlCAsInput = $true

function Handle-CtrlC {
    Write-Host "Exiting..."
    $script:running = $false
    exit 0
}

# Start a job to check for Ctrl+C
Start-Job -ScriptBlock {
    while ($true) {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if (($key.Modifiers -band [ConsoleModifiers]::Control) -and ($key.Key -eq 'C')) {
                Handle-CtrlC
            }
        }
        Start-Sleep -Milliseconds 100
    }
} | Out-Null

if ($args[0] -eq "--test") {
    while ($script:running) {
        Write-Host "Starting Hypercorn server in test environment..."
        $process = Start-Process -FilePath "hypercorn" -ArgumentList "main:app --bind 0.0.0.0:8000 --log-level debug --reload --access-log -" -RedirectStandardOutput "hypercorn.log" -RedirectStandardError "hypercorn.log" -PassThru
        
        # Monitor the log file for errors
        Get-Content "hypercorn.log" -Wait | ForEach-Object {
            Write-Host $_
            if ($_ -match "Syntax error") {
                Write-Host "Syntax error detected. Restarting server..."
                $process.Kill()
            }
        }
        
        Write-Host "Hypercorn server crashed in test environment. Restarting in 3 seconds..."
        Start-Sleep -Seconds 3
    }
}
else {
    # Get the WORKERS environment variable or default to 1
    $workers = if ($env:WORKERS) { $env:WORKERS } else { "1" }
    Write-Host "WORKERS: $workers"
    hypercorn main:app --workers $workers --bind 0.0.0.0:8000
}