# LMS Application - Restart Script (After Fixes)
# This script stops any running servers and starts them fresh

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LMS APPLICATION - RESTART (FIXED VERSION)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Function to kill processes on specific ports
function Stop-ProcessOnPort {
    param($Port)
    
    Write-Host "Checking for processes on port $Port..." -ForegroundColor Yellow
    $connections = netstat -ano | Select-String ":$Port"
    
    if ($connections) {
        foreach ($connection in $connections) {
            $parts = $connection.ToString() -split '\s+'
            $pid = $parts[-1]
            
            if ($pid -and $pid -ne "0") {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Write-Host "  Stopped process $pid on port $Port" -ForegroundColor Green
                }
                catch {
                    Write-Host "  Could not stop process $pid (may already be stopped)" -ForegroundColor Gray
                }
            }
        }
    }
    else {
        Write-Host "  No processes found on port $Port" -ForegroundColor Gray
    }
}

# Stop existing servers
Write-Host "`nStopping existing servers..." -ForegroundColor Yellow
Stop-ProcessOnPort 8001  # Backend
Stop-ProcessOnPort 8000  # Backend alt
Stop-ProcessOnPort 3000  # Frontend
Stop-ProcessOnPort 3001  # Frontend alt

Start-Sleep -Seconds 2

# Check environment
Write-Host "`nChecking environment..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "  ERROR: .env file not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "backend\.venv")) {
    Write-Host "  ERROR: Python virtual environment not found!" -ForegroundColor Red
    Write-Host "  Run: cd backend && python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "  WARNING: Node modules not found!" -ForegroundColor Yellow
    Write-Host "  Run: cd frontend && npm install" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Environment OK" -ForegroundColor Green

# Start Backend
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "STARTING BACKEND SERVER..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\backend
    .\.venv\Scripts\Activate.ps1
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
}

Write-Host "Backend starting on http://127.0.0.1:8001" -ForegroundColor Green
Write-Host "Job ID: $($backendJob.Id)" -ForegroundColor Gray

# Wait for backend to start
Write-Host "`nWaiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start Frontend  
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "STARTING FRONTEND SERVER..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm run dev
}

Write-Host "Frontend starting on http://localhost:3000" -ForegroundColor Green
Write-Host "Job ID: $($frontendJob.Id)" -ForegroundColor Gray

# Monitor servers
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SERVERS STARTING..." -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Monitoring startup (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check if jobs are still running
$backendState = (Get-Job -Id $backendJob.Id).State
$frontendState = (Get-Job -Id $frontendJob.Id).State

Write-Host "`nServer Status:" -ForegroundColor Cyan
Write-Host "  Backend: $backendState" -ForegroundColor $(if ($backendState -eq "Running") { "Green" } else { "Red" })
Write-Host "  Frontend: $frontendState" -ForegroundColor $(if ($frontendState -eq "Running") { "Green" } else { "Red" })

if ($backendState -eq "Running" -and $frontendState -eq "Running") {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "✅ ALL SERVERS STARTED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    
    Write-Host "🌐 Access your application:" -ForegroundColor Cyan
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend:  http://127.0.0.1:8001" -ForegroundColor White
    Write-Host "  API Docs: http://127.0.0.1:8001/docs`n" -ForegroundColor White
    
    Write-Host "📋 CRITICAL FIXES APPLIED:" -ForegroundColor Cyan
    Write-Host "  ✅ Cookie authentication fixed" -ForegroundColor Green
    Write-Host "  ✅ Null checks added to all endpoints" -ForegroundColor Green
    Write-Host "  ✅ Logout loop prevention" -ForegroundColor Green
    Write-Host "  ✅ System admin user type detection" -ForegroundColor Green
    Write-Host "  ✅ CORS configuration updated" -ForegroundColor Green
    
    Write-Host "`n🧪 TEST NOW:" -ForegroundColor Yellow
    Write-Host "  1. Clear browser cookies and cache" -ForegroundColor White
    Write-Host "  2. Test session creation" -ForegroundColor White
    Write-Host "  3. Test teacher creation" -ForegroundColor White
    Write-Host "  4. Test student creation" -ForegroundColor White
    Write-Host "  5. Check for random logouts`n" -ForegroundColor White
    
    Write-Host "📄 See CRITICAL_FIXES_APPLIED.md for details`n" -ForegroundColor Cyan
    
    Write-Host "Press Ctrl+C to stop servers" -ForegroundColor Yellow
    
    # Keep script running to monitor jobs
    try {
        while ($true) {
            Start-Sleep -Seconds 30
            
            $backend = Get-Job -Id $backendJob.Id
            $frontend = Get-Job -Id $frontendJob.Id
            
            if ($backend.State -ne "Running") {
                Write-Host "`n❌ Backend server stopped unexpectedly!" -ForegroundColor Red
                Receive-Job -Id $backendJob.Id
                break
            }
            
            if ($frontend.State -ne "Running") {
                Write-Host "`n❌ Frontend server stopped unexpectedly!" -ForegroundColor Red
                Receive-Job -Id $frontendJob.Id
                break
            }
        }
    }
    finally {
        Write-Host "`nStopping servers..." -ForegroundColor Yellow
        Stop-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
        Stop-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
        Write-Host "Servers stopped." -ForegroundColor Green
    }
}
else {
    Write-Host "`n❌ SERVER STARTUP FAILED!" -ForegroundColor Red
    
    if ($backendState -ne "Running") {
        Write-Host "`nBackend Output:" -ForegroundColor Yellow
        Receive-Job -Id $backendJob.Id
    }
    
    if ($frontendState -ne "Running") {
        Write-Host "`nFrontend Output:" -ForegroundColor Yellow
        Receive-Job -Id $frontendJob.Id
    }
    
    Write-Host "`nCheck the error messages above" -ForegroundColor Red
    
    # Cleanup
    Stop-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    Stop-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    
    exit 1
}
