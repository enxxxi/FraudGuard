# Start FraudGuard locally: ML service + local API + Streamlit dashboard
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

# Stop any existing processes on ports 8000, 8787, 8501 to prevent Errno 10048
Write-Host "Checking for and cleaning up any existing processes on ports 8000, 8787, 8501..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000, 8787, 8501 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" } | ForEach-Object {
    $pidToKill = $_.OwningProcess
    if ($pidToKill) {
        Write-Host "Killing process $pidToKill on port $($_.LocalPort)..." -ForegroundColor Yellow
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 1

function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )

    $safeWorkingDirectory = $WorkingDirectory.Replace("'", "''")
    $safeTitle = $Title.Replace("'", "''")

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$safeWorkingDirectory'; Write-Host '=== $safeTitle ===' -ForegroundColor Cyan; $Command"
    ) | Out-Null
}

Write-Host "Starting FraudGuard local stack..." -ForegroundColor Green

$mlDir = Join-Path $Root "backend\ml-service"
$localApiDir = Join-Path $Root "backend\local-api"

if (-not (Test-Path (Join-Path $mlDir ".venv\Scripts\python.exe"))) {
    Write-Host "Creating ML service virtual environment..."
    py -3 -m venv (Join-Path $mlDir ".venv")
    & (Join-Path $mlDir ".venv\Scripts\python.exe") -m pip install --upgrade pip
    & (Join-Path $mlDir ".venv\Scripts\pip.exe") install -r (Join-Path $mlDir "requirements.txt")
}

if (-not (Test-Path (Join-Path $localApiDir ".venv\Scripts\python.exe"))) {
    Write-Host "Creating local API virtual environment..."
    py -3 -m venv (Join-Path $localApiDir ".venv")
    & (Join-Path $localApiDir ".venv\Scripts\python.exe") -m pip install --upgrade pip
    & (Join-Path $localApiDir ".venv\Scripts\pip.exe") install -r (Join-Path $localApiDir "requirements.txt")
}

if (-not (Test-Path (Join-Path $Root ".venv\Scripts\python.exe"))) {
    Write-Host "Creating dashboard virtual environment..."
    py -3 -m venv (Join-Path $Root ".venv")
    & (Join-Path $Root ".venv\Scripts\python.exe") -m pip install --upgrade pip
    & (Join-Path $Root ".venv\Scripts\pip.exe") install -r (Join-Path $Root "requirements.txt")
}

Start-ServiceWindow -Title "ML Service :8000" -WorkingDirectory $mlDir -Command ".\.venv\Scripts\uvicorn.exe app:app --host 127.0.0.1 --port 8000"
Start-Sleep -Seconds 3
Start-ServiceWindow -Title "Local API :8787" -WorkingDirectory $localApiDir -Command "`$env:ML_SERVICE_URL='http://127.0.0.1:8000'; .\.venv\Scripts\uvicorn.exe app:app --host 127.0.0.1 --port 8787"
Start-Sleep -Seconds 2

$env:FRAUDGUARD_API_BASE_URL = "http://127.0.0.1:8787"
$env:FRAUDGUARD_USER_ID = "demo-user"

Write-Host "Seeding demo transactions..."
& (Join-Path $Root ".venv\Scripts\python.exe") (Join-Path $Root "scripts\seed_demo_data.py")

Write-Host "Launching Streamlit dashboard at http://localhost:8501"
Start-ServiceWindow -Title "Streamlit :8501" -WorkingDirectory $Root -Command "`$env:FRAUDGUARD_API_BASE_URL='http://127.0.0.1:8787'; `$env:FRAUDGUARD_USER_ID='demo-user'; .\.venv\Scripts\python.exe -m streamlit run app.py"

Write-Host ""
Write-Host "FraudGuard is starting in separate terminals." -ForegroundColor Green
Write-Host "  ML service:  http://127.0.0.1:8000/health"
Write-Host "  Local API:   http://127.0.0.1:8787/health"
Write-Host "  Dashboard:   http://localhost:8501"
