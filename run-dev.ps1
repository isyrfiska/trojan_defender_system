# Run both backend (Django) and frontend (Vite) development servers simultaneously
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPython = Join-Path $root ".venv\Scripts\python.exe"
$backendManage = Join-Path $root "backend\manage.py"
$frontendDir = Join-Path $root "frontend"

if (-Not (Test-Path $backendPython)) {
    Write-Host "Python venv not found at $backendPython. Please create and activate the venv, then re-run this script." -ForegroundColor Red
    exit 1
}

# Start backend server
Write-Host "Starting Django backend on port $BackendPort..." -ForegroundColor Cyan
$backendArgs = @($backendManage, 'runserver', "0.0.0.0:$BackendPort")
$backendProc = Start-Process -FilePath $backendPython -ArgumentList $backendArgs -WorkingDirectory $root -PassThru

# Start frontend server
Write-Host "Starting Vite frontend on port $FrontendPort..." -ForegroundColor Cyan
$frontendProc = Start-Process -FilePath "npm" -ArgumentList @('run','dev') -WorkingDirectory $frontendDir -PassThru

Write-Host "\nServers launching..." -ForegroundColor Green
Write-Host "Backend: http://localhost:$BackendPort/" -ForegroundColor Green
Write-Host "Frontend: http://localhost:$FrontendPort/" -ForegroundColor Green
Write-Host "\nUse Ctrl+C in each terminal to stop the servers."