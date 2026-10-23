param(
    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"
$CodeRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvRoot = Join-Path $CodeRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$WebRoot = Join-Path $CodeRoot "apps\web"

function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Local setup command failed with exit code $LASTEXITCODE."
    }
}

if (-not $PythonPath) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) { $PythonPath = $PythonCommand.Source }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python 3.11+ was not found. Re-run with -PythonPath C:\path\to\python.exe"
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Invoke-Checked { & $PythonPath -m venv $VenvRoot }
}

Invoke-Checked { & $VenvPython -m pip install --upgrade pip }
Invoke-Checked { & $VenvPython -m pip install -e (Join-Path $CodeRoot "packages\core_engine") }
Invoke-Checked { & $VenvPython -m pip install -e "${CodeRoot}[run,test]" }

Push-Location $WebRoot
try {
    Invoke-Checked { npm ci }
} finally {
    Pop-Location
}

Write-Host "Local dependencies are ready. Run scripts\start_local.ps1"
