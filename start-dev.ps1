# Learnlyf - Development Startup Script
# This script starts both backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Learnlyf - Phase 1 MVP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend directory exists
if (-not (Test-Path "backend")) {
    Write-Host "❌ Backend directory not found!" -ForegroundColor Red
    exit 1
}

# Check if frontend directory exists
if (-not (Test-Path "frontend")) {
    Write-Host "❌ Frontend directory not found!" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Starting Learnlyf..." -ForegroundColor Green
Write-Host ""

# Function to start backend
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location backend
    Write-Host "🚀 Starting Backend Server..." -ForegroundColor Yellow
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
}

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Function to start frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location frontend
    Write-Host "🎨 Starting Frontend Server..." -ForegroundColor Yellow
    npm run dev
}

Write-Host ""
Write-Host "✅ Backend starting on: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "✅ Frontend starting on: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "📚 API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "📚 Health Check: http://127.0.0.1:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔑 Demo Accounts:" -ForegroundColor Yellow
Write-Host "   System Admin: admin@learnlyf.com / Admin123!@#" -ForegroundColor White
Write-Host "   School Admin: admin@demo-school.com / Admin123!@#" -ForegroundColor White
Write-Host ""
Write-Host "⏳ Waiting for servers to start..." -ForegroundColor Yellow
Write-Host "   (This may take 10-20 seconds)" -ForegroundColor Gray
Write-Host ""

# Wait for jobs to produce output
Start-Sleep -Seconds 10

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Servers are starting!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Check the output above for any errors" -ForegroundColor Yellow
Write-Host "🌐 Open http://localhost:3000 in your browser" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Gray
Write-Host ""

# Keep script running and display job output
try {
    while ($true) {
        $backendOutput = Receive-Job -Job $backendJob
        $frontendOutput = Receive-Job -Job $frontendJob
        
        if ($backendOutput) {
            Write-Host "[Backend] $backendOutput" -ForegroundColor Blue
        }
        if ($frontendOutput) {
            Write-Host "[Frontend] $frontendOutput" -ForegroundColor Magenta
        }
        
        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host ""
    Write-Host "🛑 Stopping servers..." -ForegroundColor Red
    Stop-Job -Job $backendJob
    Stop-Job -Job $frontendJob
    Remove-Job -Job $backendJob
    Remove-Job -Job $frontendJob
    Write-Host "✅ All servers stopped" -ForegroundColor Green
}
