# Start the API locally with hot reload.
# Usage: .\scripts\dev-api.ps1
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot "services\api"
$venvPython = Join-Path $apiDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found. Run .\scripts\setup-api.ps1 first." -ForegroundColor Red
    exit 1
}

# Load .env into the process environment (simple KEY=VALUE parser)
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$' -and $_ -notmatch '^\s*#') {
            [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
        }
    }
}

Push-Location $apiDir
try {
    & $venvPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
