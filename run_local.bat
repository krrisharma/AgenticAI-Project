@echo off
echo ========================================================
echo Starting ClearPath (Delhi Traffic & Air Quality Manager)
echo ========================================================

set SCRIPT_DIR=%~dp0

echo [1/2] Starting Backend FastAPI Server on http://localhost:8000 ...
start "ClearPath Backend (FastAPI)" cmd /k "cd /d "%SCRIPT_DIR%backend" && set PYTHONPATH=%SCRIPT_DIR%;%SCRIPT_DIR%backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Frontend Vite Server on http://localhost:5173 ...
start "ClearPath Frontend (React/Vite)" cmd /k "cd /d "%SCRIPT_DIR%frontend" && npm run dev"

echo.
echo ========================================================
echo Both servers have been launched in separate windows!
echo - Frontend: http://localhost:5173
echo - Backend API Docs: http://localhost:8000/docs
echo ========================================================
