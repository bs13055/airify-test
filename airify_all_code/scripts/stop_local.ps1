$ErrorActionPreference = "Stop"
$CodeRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateFile = Join-Path $CodeRoot "data\local\local-runtime.json"

if (-not (Test-Path -LiteralPath $StateFile)) {
    Write-Host "Airify LOCAL is not running (no runtime state file)."
    exit 0
}

$State = Get-Content -Raw -LiteralPath $StateFile | ConvertFrom-Json
$Targets = @(
    @{ Port = 8000; ExpectedPid = [int]$State.api_pid; Signature = "uvicorn app.main:app" },
    @{ Port = 5173; ExpectedPid = [int]$State.web_pid; Signature = "vite" }
)
foreach ($Target in $Targets) {
    $Listener = Get-NetTCPConnection -LocalPort $Target.Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $Listener) { continue }
    if ($Listener.OwningProcess -ne $Target.ExpectedPid) {
        Write-Warning "Port $($Target.Port) is owned by a different process; it was not stopped."
        continue
    }
    $Process = Get-CimInstance Win32_Process -Filter "ProcessId = $($Listener.OwningProcess)"
    if ($Process.CommandLine -notlike "*$($Target.Signature)*") {
        Write-Warning "Process on port $($Target.Port) is not recognized as Airify; it was not stopped."
        continue
    }
    Stop-Process -Id $Listener.OwningProcess
}
Remove-Item -LiteralPath $StateFile
Write-Host "Airify LOCAL stopped."
