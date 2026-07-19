# Start Both Servers Script
# This will open two new terminal windows for backend and frontend

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  STARTING LEARNLYF SERVERS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$backendPath = "c:\Users\DELL\Downloads\LMS\backend"
$frontendPath = "c:\Users\DELL\Downloads\LMS\frontend"

# Check if paths exist
if (-not (Test-Path $backendPath)) {
    Write-Host "[ERROR] Backend directory not found!" -ForegroundColor Red
    exit
}

if (-not (Test-Path $frontendPath)) {
    Write-Host "[ERROR] Frontend directory not found!" -ForegroundColor Red
    exit
}

Write-Host "Step 1: Starting Backend Server..." -ForegroundColor Yellow
Write-Host "  Location: $backendPath" -ForegroundColor Gray

# Start backend in new PowerShell window
$backendCommand = "cd '$backendPath'; .venv\Scripts\activate; Write-Host 'Backend starting...' -ForegroundColor Green; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

Write-Host "  ✓ Backend terminal opened`n" -ForegroundColor Green

Start-Sleep -Seconds 2

Write-Host "Step 2: Starting Frontend Server..." -ForegroundColor Yellow
Write-Host "  Location: $frontendPath" -ForegroundColor Gray

# Start frontend in new PowerShell window
$frontendCommand = "cd '$frontendPath'; Write-Host 'Frontend starting...' -ForegroundColor Green; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "  ✓ Frontend terminal opened`n" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SERVERS STARTING..." -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Two new terminal windows have opened:" -ForegroundColor White
Write-Host "  1. Backend - Wait for: 'Application startup complete'" -ForegroundColor White
Write-Host "  2. Frontend - Wait for: 'Ready in 3s'" -ForegroundColor White
Write-Host "`n"

Write-Host "After both servers start:" -ForegroundColor Yellow
Write-Host "  • Backend:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  • Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "`n"

Write-Host "To run tests after servers start:" -ForegroundColor Yellow
Write-Host "  python test_system.py" -ForegroundColor White
Write-Host "`n"

Write-Host "Keep both terminal windows open!" -ForegroundColor Green
Write-Host "Press any key to close this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
