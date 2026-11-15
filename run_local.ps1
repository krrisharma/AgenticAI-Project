# PowerShell launcher for ClearPath local development
$scriptDir = $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Green
Write-Host "Starting ClearPath (Delhi Traffic & Air Quality Manager)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

Write-Host "`n[1/2] Starting Backend FastAPI Server on http://localhost:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='$scriptDir;$scriptDir\backend'; Set-Location '$scriptDir\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Frontend Vite Server on http://localhost:5173 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$scriptDir\frontend'; npm run dev"

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "Both servers started in separate terminal windows!" -ForegroundColor Green
Write-Host " - Frontend UI:        http://localhost:5173" -ForegroundColor Yellow
Write-Host " - Backend Swagger API: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
