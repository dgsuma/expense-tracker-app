# One-time (or refresh) setup of the API Python environment.
# Usage: .\scripts\setup-api.ps1
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot "services\api"

Push-Location $apiDir
try {
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating virtual environment..."
        py -3.12 -m venv .venv
    }
    $venvPython = Join-Path $apiDir ".venv\Scripts\python.exe"
    Write-Host "Installing dependencies..."
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements-dev.txt
    Write-Host "Done. Activate with: services\api\.venv\Scripts\Activate.ps1" -ForegroundColor Green
} finally {
    Pop-Location
}
