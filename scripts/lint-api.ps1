# Lint and format-check the API code.
# Usage: .\scripts\lint-api.ps1 [-Fix]
param([switch]$Fix)
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot "services\api"
$venvPython = Join-Path $apiDir ".venv\Scripts\python.exe"

Push-Location $apiDir
try {
    if ($Fix) {
        & $venvPython -m ruff check --fix .
        & $venvPython -m ruff format .
    } else {
        & $venvPython -m ruff check .
        & $venvPython -m ruff format --check .
    }
} finally {
    Pop-Location
}
