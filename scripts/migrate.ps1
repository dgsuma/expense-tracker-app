# Database migration helper. Run from anywhere:
#   .\scripts\migrate.ps1 upgrade            # apply all migrations (default)
#   .\scripts\migrate.ps1 revision "msg"     # autogenerate a new migration
#   .\scripts\migrate.ps1 downgrade          # roll back one migration
#   .\scripts\migrate.ps1 current            # show current revision
#   .\scripts\migrate.ps1 seed               # seed system default categories
param([string]$Command = "upgrade", [string]$Message = "")
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$dbDir = Join-Path $repoRoot "database"
$venvPython = Join-Path $repoRoot "services\api\.venv\Scripts\python.exe"

# Load .env into the process environment
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$' -and $_ -notmatch '^\s*#') {
            [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
        }
    }
}

Push-Location $dbDir
try {
    switch ($Command) {
        "upgrade"   { & $venvPython -m alembic upgrade head }
        "downgrade" { & $venvPython -m alembic downgrade -1 }
        "current"   { & $venvPython -m alembic current }
        "history"   { & $venvPython -m alembic history }
        "revision"  {
            if (-not $Message) { Write-Host "Usage: migrate.ps1 revision `"message`"" -ForegroundColor Red; exit 1 }
            & $venvPython -m alembic revision --autogenerate -m $Message
        }
        "seed"      { & $venvPython (Join-Path $dbDir "seeds\seed.py") }
        default     { Write-Host "Unknown command: $Command" -ForegroundColor Red; exit 1 }
    }
} finally {
    Pop-Location
}
