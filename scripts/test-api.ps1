# Run the API test suite.
# Usage: .\scripts\test-api.ps1
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot "services\api"
$venvPython = Join-Path $apiDir ".venv\Scripts\python.exe"

Push-Location $apiDir
try {
    & $venvPython -m pytest
} finally {
    Pop-Location
}
