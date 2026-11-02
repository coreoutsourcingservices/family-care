# FamilyCare - Windows PowerShell launcher. Usage: .\start-backend.ps1 [-Install] [-CheckOnly]
param([switch]$Install, [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    $python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
}
if (-not (Test-Path $python)) {
    Write-Host 'Creating backend/venv using Windows Python...' -ForegroundColor Cyan
    py -3 -m venv venv
    $python = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
}
if ($Install) {
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
if (-not (Test-Path '.env')) {
    Write-Host 'Creating local .env with fresh random signing secrets...' -ForegroundColor Yellow
    & $python scripts/configure_local.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
& $python scripts/diagnose.py
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Resolve checks above, then restart. Use -Install if Python modules are missing.' -ForegroundColor Yellow
    exit 1
}
if ($CheckOnly) { & $python server.py --check } else { & $python server.py }
exit $LASTEXITCODE
