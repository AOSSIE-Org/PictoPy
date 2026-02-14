Write-Host "Starting PictoPy Master Orchestrator..." -ForegroundColor Cyan
$root = $PSScriptRoot
$OriginalDir = Get-Location

# 1. Start Backend & Sync as background jobs
$BackendJob = Start-Job -Name "Backend" -ScriptBlock {
    cd "$using:root\backend"
    .\.env\Scripts\Activate.ps1
    uvicorn main:app --host 127.0.0.1 --port 52123
}

$SyncJob = Start-Job -Name "Sync" -ScriptBlock {
    cd "$using:root\sync-microservice"
    .\.sync-env\Scripts\Activate.ps1
    uvicorn main:app --host 127.0.0.1 --port 52124
}

# Clean Exit handling
$null = Register-EngineEvent PowerShell.Exiting -Action {
    Get-Job | Stop-Job -ErrorAction SilentlyContinue
}

try {
    cd "$root\frontend"
    # Launch Tauri as the Master process
    $TauriProc = Start-Process cmd.exe -ArgumentList "/c npm run tauri dev" -PassThru -NoNewWindow

    # --- BUFFER INITIALIZATION ---
    $bufferLog = $null
    $repeatCount = 1

    while (-not $TauriProc.HasExited) {
        # Check for service crashes
        if ((Get-Job -Name "Backend").State -eq "Failed") { throw "Backend crashed!" }
        if ((Get-Job -Name "Sync").State -eq "Failed") { throw "Sync service crashed!" }

        # 1. Fetch from each job separately into an array to keep them distinct
        $rawLogs = @()
        $rawLogs += Receive-Job -Name "Backend"
        $rawLogs += Receive-Job -Name "Sync"

        foreach ($line in $rawLogs) {
            # 2. Cast to string and trim to handle non-string objects safely
            $trimmedLine = "$line".Trim()
            if ([string]::IsNullOrWhiteSpace($trimmedLine)) { continue }

            if ($trimmedLine -ne $bufferLog) {
                # 3. Print the summary if the previous sequence ended
                if ($null -ne $bufferLog -and $repeatCount -gt 1) {
                    Write-Host "[TOTAL x$repeatCount] $bufferLog" -ForegroundColor Gray
                }

                # 4. Print the NEW log immediately on its own line
                $logColor = if ($trimmedLine -match "BACKEND") { "Cyan" } else { "Yellow" }
                Write-Host $trimmedLine -ForegroundColor $logColor

                # Update trackers
                $bufferLog = $trimmedLine
                $repeatCount = 1
            } else {
                # 5. Same log? Just keep counting
                $repeatCount++
            }
        }
        Start-Sleep -Milliseconds 500
    }
}
catch {
    Write-Host "`nCRITICAL ERROR: $_" -ForegroundColor White -BackgroundColor Red
}
finally {
    # FLUSH: If the app closed while a repeat was active, print the final count
    if ($repeatCount -gt 1) {
        Write-Host "[REPEAT x$($repeatCount - 1)] $bufferLog" -ForegroundColor Gray
    }

    # 2. AUTOMATED CLEANUP
    Write-Host "`nPictoPy closed. Cleaning up all services..." -ForegroundColor Red
    
    Get-Job | Stop-Job -ErrorAction SilentlyContinue
    Get-Job | Remove-Job -Force
    
    # Force-kill ports 52123 & 52124
    Get-NetTCPConnection -LocalPort 52123, 52124 -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }

    # 3. RETURN TO PROJECT ROOT
    Set-Location $OriginalDir
    Write-Host "All services stopped. Returned to: $(Get-Location)" -ForegroundColor Green
}