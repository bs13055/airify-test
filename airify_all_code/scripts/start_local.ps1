$ErrorActionPreference = "Stop"
$CodeRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $CodeRoot ".venv\Scripts\python.exe"
$WebRoot = Join-Path $CodeRoot "apps\web"
$RuntimeRoot = Join-Path $CodeRoot "data\local"
$StateFile = Join-Path $RuntimeRoot "local-runtime.json"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Local Python environment is missing. Run scripts\setup_local.ps1 first."
}
if (-not (Test-Path -LiteralPath (Join-Path $WebRoot "node_modules"))) {
    throw "Frontend dependencies are missing. Run scripts\setup_local.ps1 first."
}
if (Test-Path -LiteralPath $StateFile) {
    throw "A local runtime state file already exists. Run scripts\stop_local.ps1 first."
}
foreach ($Port in @(8000, 5173)) {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port is already in use. Stop the existing service before starting Airify LOCAL."
    }
}

New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
$ApiOut = Join-Path $RuntimeRoot "api.out.log"
$ApiErr = Join-Path $RuntimeRoot "api.err.log"
$WebOut = Join-Path $RuntimeRoot "web.out.log"
$WebErr = Join-Path $RuntimeRoot "web.err.log"

$Api = Start-Process -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--app-dir", "apps/api", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $CodeRoot -WindowStyle Hidden -RedirectStandardOutput $ApiOut -RedirectStandardError $ApiErr -PassThru
$Web = Start-Process -FilePath "npm.cmd" `
    -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1") `
    -WorkingDirectory $WebRoot -WindowStyle Hidden -RedirectStandardOutput $WebOut -RedirectStandardError $WebErr -PassThru

$ApiReady = $false
for ($Attempt = 0; $Attempt -lt 20; $Attempt++) {
    try {
        $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/healthz" -TimeoutSec 2
        if ($Health) { $ApiReady = $true; break }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}
$WebReady = $false
for ($Attempt = 0; $Attempt -lt 20; $Attempt++) {
    try {
        $Page = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -TimeoutSec 2 -UseBasicParsing
        if ($Page.StatusCode -eq 200) { $WebReady = $true; break }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}
if (-not $ApiReady -or -not $WebReady) {
    Stop-Process -Id $Api.Id, $Web.Id -ErrorAction SilentlyContinue
    throw "Airify LOCAL did not become ready. Check data\local\*.err.log."
}

$ApiPid = (Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object -First 1).OwningProcess
$WebPid = (Get-NetTCPConnection -LocalPort 5173 -State Listen | Select-Object -First 1).OwningProcess
@{
    api_pid = $ApiPid
    web_pid = $WebPid
    api_launcher_pid = $Api.Id
    web_launcher_pid = $Web.Id
    started_at = (Get-Date).ToString("o")
} | ConvertTo-Json | Set-Content -LiteralPath $StateFile -Encoding utf8

Write-Host "Airify LOCAL is running:"
Write-Host "  Health App: http://127.0.0.1:5173/?mock=health#/health"
Write-Host "  API docs:   http://127.0.0.1:8000/docs"
Write-Host "  Stop:       scripts\stop_local.ps1"
