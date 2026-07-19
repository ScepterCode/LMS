# Quick Test Runner for Learnlyf
# This script helps you test the system

Write-Host "`n" -NoNewline
Write-Host "=====================================================================" -ForegroundColor Blue
Write-Host "           LEARNLYF - TESTING HELPER SCRIPT" -ForegroundColor Blue
Write-Host "=====================================================================" -ForegroundColor Blue
Write-Host "`n"

# Check if servers are running
Write-Host "STEP 1: Checking if servers are running..." -ForegroundColor Yellow
Write-Host "`n"

# Check backend
Write-Host "Checking backend (localhost:8000)..." -ForegroundColor Cyan
try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  [OK] Backend is running!" -ForegroundColor Green
    $backendRunning = $true
} catch {
    Write-Host "  [ERROR] Backend is NOT running!" -ForegroundColor Red
    Write-Host "  Please start the backend first:" -ForegroundColor Yellow
    Write-Host "    cd backend" -ForegroundColor White
    Write-Host "    .venv\Scripts\activate" -ForegroundColor White
    Write-Host "    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
    $backendRunning = $false
}

Write-Host "`n"

# Check frontend
Write-Host "Checking frontend (localhost:3000)..." -ForegroundColor Cyan
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  [OK] Frontend is running!" -ForegroundColor Green
    $frontendRunning = $true
} catch {
    Write-Host "  [ERROR] Frontend is NOT running!" -ForegroundColor Red
    Write-Host "  Please start the frontend first:" -ForegroundColor Yellow
    Write-Host "    cd frontend" -ForegroundColor White
    Write-Host "    npm run dev" -ForegroundColor White
    $frontendRunning = $false
}

Write-Host "`n"
Write-Host "=====================================================================" -ForegroundColor Blue
Write-Host "`n"

if (-not $backendRunning -or -not $frontendRunning) {
    Write-Host "[ERROR] Cannot proceed with testing until both servers are running." -ForegroundColor Red
    Write-Host "`n"
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# Both servers are running
Write-Host "STEP 2: Choose testing method" -ForegroundColor Yellow
Write-Host "`n"
Write-Host "1. Run automated API tests (Python script)" -ForegroundColor White
Write-Host "2. Open manual testing checklist" -ForegroundColor White
Write-Host "3. Open application in browser for manual testing" -ForegroundColor White
Write-Host "4. Run all tests (automated + open browser)" -ForegroundColor White
Write-Host "5. Exit" -ForegroundColor White
Write-Host "`n"

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`n"
        Write-Host "Running automated tests..." -ForegroundColor Yellow
        Write-Host "`n"
        
        # Check if Python is installed
        try {
            $pythonVersion = python --version 2>&1
            Write-Host "Python found: $pythonVersion" -ForegroundColor Green
            Write-Host "`n"
            
            # Run the test script
            python test_system.py
        } catch {
            Write-Host "[ERROR] Python not found!" -ForegroundColor Red
            Write-Host "Please install Python 3.8+ to run automated tests." -ForegroundColor Yellow
        }
    }
    "2" {
        Write-Host "`n"
        Write-Host "Opening manual testing checklist..." -ForegroundColor Yellow
        Start-Process "MANUAL_TESTING_CHECKLIST.md"
    }
    "3" {
        Write-Host "`n"
        Write-Host "Opening application in browser..." -ForegroundColor Yellow
        Start-Process "http://localhost:3000"
        Write-Host "`n"
        Write-Host "Login credentials:" -ForegroundColor Cyan
        Write-Host "  Email: sarahchidiloveday@gmail.com" -ForegroundColor White
        Write-Host "  Password: Admin123!" -ForegroundColor White
    }
    "4" {
        Write-Host "`n"
        Write-Host "Running all tests..." -ForegroundColor Yellow
        Write-Host "`n"
        
        # Open browser
        Write-Host "Opening application in browser..." -ForegroundColor Cyan
        Start-Process "http://localhost:3000"
        
        # Open checklist
        Write-Host "Opening manual testing checklist..." -ForegroundColor Cyan
        Start-Process "MANUAL_TESTING_CHECKLIST.md"
        
        # Run automated tests
        Write-Host "Running automated tests..." -ForegroundColor Cyan
        Write-Host "`n"
        
        try {
            python test_system.py
        } catch {
            Write-Host "[WARNING] Could not run automated tests (Python not found)" -ForegroundColor Yellow
        }
    }
    "5" {
        Write-Host "`nExiting..." -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "`n[ERROR] Invalid choice!" -ForegroundColor Red
    }
}

Write-Host "`n"
Write-Host "=====================================================================" -ForegroundColor Blue
Write-Host "                          TESTING COMPLETE" -ForegroundColor Blue
Write-Host "=====================================================================" -ForegroundColor Blue
Write-Host "`n"
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Check the test results above" -ForegroundColor White
Write-Host "  2. Review MANUAL_TESTING_CHECKLIST.md for detailed steps" -ForegroundColor White
Write-Host "  3. Report any issues you find" -ForegroundColor White
Write-Host "`n"
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
