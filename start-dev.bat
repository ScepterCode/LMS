@echo off
REM Nigerian LMS - Development Startup Script (CMD Version)
REM This script starts both backend and frontend servers

echo ========================================
echo    Nigerian LMS - Phase 1 MVP
echo ========================================
echo.

echo Starting Backend Server...
start "Backend" cmd /k "cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak > nul

echo Starting Frontend Server...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo    Servers Starting!
echo ========================================
echo.
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:3000
echo API Docs: http://127.0.0.1:8000/docs
echo.
echo Demo Accounts:
echo   System Admin: admin@nigerianlms.com / Admin123!@#
echo   School Admin: admin@demo-school.com / Admin123!@#
echo.
echo Press any key to open the application in browser...
pause > nul

start http://localhost:3000

echo.
echo Application is now running!
echo Close the Backend and Frontend windows to stop the servers.
echo.
pause
