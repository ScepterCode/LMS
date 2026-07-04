#!/usr/bin/env pwsh
# Restart Both Servers Script

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  RESTARTING LMS SERVERS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Kill existing processes on ports 3000 and 8001
Write-Host "🔍 Checking for existing processes..." -ForegroundColor Yellow

# Kill process on port 8001 (Backend)
try {
    $backend = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($backend) {
        Write-Host "   Stopping existing backend process (PID: $backend)..." -ForegroundColor Gray
        Stop-Process -Id $backend -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Host "   ✅ Backend process stopped" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  No backend process found on port 8001" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ℹ️  No backend process to stop" -ForegroundColor Gray
}

# Kill process on port 3000 (Frontend)
try {
    $frontend = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($frontend) {
        Write-Host "   Stopping existing frontend process (PID: $frontend)..." -ForegroundColor Gray
        Stop-Process -Id $frontend -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Host "   ✅ Frontend process stopped" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  No frontend process found on port 3000" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ℹ️  No frontend process to stop" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🚀 Starting servers..." -ForegroundColor Cyan
Write-Host ""

# Check if directories exist
if (!(Test-Path ".\backend")) {
    Write-Host "❌ Error: backend directory not found!" -ForegroundColor Red
    exit 1
}

if (!(Test-Path ".\frontend")) {
    Write-Host "❌ Error: frontend directory not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Directories verified" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Backend on http://127.0.0.1:8001 ..." -ForegroundColor Yellow
Write-Host "Starting Frontend on http://localhost:3000 ..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Instructions
Write-Host "⚠️  IMPORTANT: This script will open TWO new terminal windows:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   1️⃣  Backend Terminal (Python/FastAPI)" -ForegroundColor White
Write-Host "   2️⃣  Frontend Terminal (Next.js)" -ForegroundColor White
Write-Host ""
Write-Host "Keep both terminals open while using the application." -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Press Enter to start both servers"

Write-Host ""
Write-Host "🚀 Starting Backend..." -ForegroundColor Green

# Start Backend in new terminal
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\DELL\Downloads\LMS\backend'; Write-Host '🐍 Activating Python Virtual Environment...' -ForegroundColor Cyan; .\.venv\Scripts\Activate.ps1; Write-Host '✅ Virtual Environment Activated' -ForegroundColor Green; Write-Host ''; Write-Host '🚀 Starting FastAPI Backend Server...' -ForegroundColor Cyan; Write-Host '   URL: http://127.0.0.1:8001' -ForegroundColor Yellow; Write-Host '   Docs: http://127.0.0.1:8001/docs' -ForegroundColor Yellow; Write-Host ''; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"

Write-Host "   ✅ Backend terminal opened" -ForegroundColor Green
Write-Host "   Waiting 3 seconds for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "🚀 Starting Frontend..." -ForegroundColor Green

# Start Frontend in new terminal  
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\DELL\Downloads\LMS\frontend'; Write-Host '⚛️  Starting Next.js Development Server...' -ForegroundColor Cyan; Write-Host '   URL: http://localhost:3000' -ForegroundColor Yellow; Write-Host ''; npm run dev"

Write-Host "   ✅ Frontend terminal opened" -ForegroundColor Green

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SERVERS STARTING..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Please wait 15-30 seconds for servers to fully start" -ForegroundColor Yellow
Write-Host ""
Write-Host "📍 Backend URL:  http://127.0.0.1:8001" -ForegroundColor Green
Write-Host "📍 API Docs:     http://127.0.0.1:8001/docs" -ForegroundColor Green
Write-Host "📍 Frontend URL: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Check the new terminal windows for startup logs" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 VERIFY NEW ENDPOINTS:" -ForegroundColor Yellow
Write-Host "   Visit http://127.0.0.1:8001/docs" -ForegroundColor White
Write-Host "   Look for:" -ForegroundColor White
Write-Host "     - 'User Management' section (5 endpoints)" -ForegroundColor White
Write-Host "     - 'Integrated Registration' section (3 endpoints)" -ForegroundColor White
Write-Host ""
Write-Host "💡 TIP: Keep both terminal windows open!" -ForegroundColor Cyan
Write-Host "    Close them to stop the servers" -ForegroundColor Gray
Write-Host ""
