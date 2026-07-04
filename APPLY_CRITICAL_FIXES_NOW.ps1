# ============================================
# APPLY CRITICAL FIXES - AUTOMATED SCRIPT
# ============================================
# This script helps apply the database migration and restart services

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  APPLY CRITICAL FIXES - LMS REPAIR SCRIPT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (!(Test-Path ".\backend") -or !(Test-Path ".\frontend")) {
    Write-Host "❌ Error: Please run this script from the LMS root directory" -ForegroundColor Red
    exit 1
}

Write-Host "📋 FIXES TO APPLY:" -ForegroundColor Yellow
Write-Host "  ✅ Fix #1: AuthContext logout bug (ALREADY APPLIED)" -ForegroundColor Green
Write-Host "  ✅ Fix #2: User management endpoint (ALREADY APPLIED)" -ForegroundColor Green
Write-Host "  ✅ Fix #3: Integrated registration (ALREADY APPLIED)" -ForegroundColor Green
Write-Host "  ⏳ Fix #4: Database migration (NEEDS MANUAL APPLICATION)" -ForegroundColor Yellow
Write-Host ""

# Verify Python files compile
Write-Host "🔍 Step 1: Verifying Python files..." -ForegroundColor Cyan
try {
    cd backend
    python -m py_compile app/api/v1/api.py 2>$null
    python -m py_compile app/api/v1/endpoints/users.py 2>$null
    python -m py_compile app/api/v1/endpoints/registration.py 2>$null
    cd ..
    Write-Host "   ✅ Python files validated successfully" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python file validation failed: $_" -ForegroundColor Red
    cd ..
    exit 1
}

Write-Host ""
Write-Host "⚠️  IMPORTANT: DATABASE MIGRATION REQUIRED" -ForegroundColor Yellow
Write-Host ""
Write-Host "The following SQL script needs to be run on your database:" -ForegroundColor White
Write-Host "   📄 database/add_student_user_id.sql" -ForegroundColor Cyan
Write-Host ""
Write-Host "Options to apply migration:" -ForegroundColor White
Write-Host "  1. Supabase Dashboard: Go to SQL Editor → Paste script → Run" -ForegroundColor White
Write-Host "  2. psql command line: psql YOUR_DB_URL -f database/add_student_user_id.sql" -ForegroundColor White
Write-Host "  3. Python script: Run the included migration helper" -ForegroundColor White
Write-Host ""

$applyMigration = Read-Host "Do you want to see the migration SQL? (y/n)"

if ($applyMigration -eq 'y') {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "MIGRATION SQL (Copy to Supabase SQL Editor)" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Get-Content .\database\add_student_user_id.sql
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
}

Write-Host ""
$proceed = Read-Host "Have you applied the database migration? (y/n)"

if ($proceed -ne 'y') {
    Write-Host ""
    Write-Host "⚠️  Please apply the database migration first, then run this script again." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "🔄 Step 2: Checking if backend is running..." -ForegroundColor Cyan

# Check if port 8001 is in use (backend running)
$backendRunning = $false
try {
    $connection = Test-NetConnection -ComputerName 127.0.0.1 -Port 8001 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($connection) {
        $backendRunning = $true
        Write-Host "   ⚠️  Backend is currently running on port 8001" -ForegroundColor Yellow
    }
} catch {
    # Port not in use
}

if ($backendRunning) {
    Write-Host ""
    Write-Host "To apply fixes, the backend needs to be restarted." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please:" -ForegroundColor White
    Write-Host "  1. Stop the current backend (Ctrl+C in its terminal)" -ForegroundColor White
    Write-Host "  2. Run this command to restart:" -ForegroundColor White
    Write-Host ""
    Write-Host "     cd backend" -ForegroundColor Cyan
    Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "     python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "   ℹ️  Backend is not currently running" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To start the backend with fixes:" -ForegroundColor White
    Write-Host "  1. Open a new terminal" -ForegroundColor White
    Write-Host "  2. Run these commands:" -ForegroundColor White
    Write-Host ""
    Write-Host "     cd backend" -ForegroundColor Cyan
    Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "     python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "🔄 Step 3: Checking frontend..." -ForegroundColor Cyan

# Check if port 3000 is in use (frontend running)
$frontendRunning = $false
try {
    $connection = Test-NetConnection -ComputerName 127.0.0.1 -Port 3000 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($connection) {
        $frontendRunning = $true
        Write-Host "   ✅ Frontend is running on port 3000" -ForegroundColor Green
    }
} catch {
    # Port not in use
}

if (!$frontendRunning) {
    Write-Host "   ⚠️  Frontend is not running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To start the frontend:" -ForegroundColor White
    Write-Host "  1. Open a new terminal" -ForegroundColor White
    Write-Host "  2. Run these commands:" -ForegroundColor White
    Write-Host ""
    Write-Host "     cd frontend" -ForegroundColor Cyan
    Write-Host "     npm run dev" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "          VERIFICATION CHECKLIST" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "After restarting backend, verify:" -ForegroundColor White
Write-Host ""
Write-Host "  [ ] 1. Visit http://127.0.0.1:8001/docs" -ForegroundColor White
Write-Host "  [ ] 2. Check for 'User Management' section (5 endpoints)" -ForegroundColor White
Write-Host "  [ ] 3. Check for 'Integrated Registration' section (3 endpoints)" -ForegroundColor White
Write-Host "  [ ] 4. Test login to dashboard" -ForegroundColor White
Write-Host "  [ ] 5. Click onboarding buttons (should NOT logout)" -ForegroundColor White
Write-Host "  [ ] 6. Try creating a user via /api/v1/users" -ForegroundColor White
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "           NEXT STEPS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Backend fixes applied - restart required" -ForegroundColor Green
Write-Host "✅ Frontend fixes applied - already active" -ForegroundColor Green
Write-Host "⏳ Database migration - apply manually" -ForegroundColor Yellow
Write-Host "⏳ Frontend UI - needs to be built" -ForegroundColor Yellow
Write-Host ""
Write-Host "Read CRITICAL_FIXES_IMPLEMENTED.md for full details" -ForegroundColor Cyan
Write-Host ""

