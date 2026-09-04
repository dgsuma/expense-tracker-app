# Run the Flutter app. Usage:
#   .\scripts\dev-app.ps1              # web (Chrome) against localhost:8000
#   .\scripts\dev-app.ps1 -Device android  # Android emulator (uses 10.0.2.2)
param([string]$Device = "chrome")
$ErrorActionPreference = "Stop"

$env:Path = "C:\flutter\bin;$env:Path"
$appDir = Join-Path (Split-Path -Parent $PSScriptRoot) "apps\mobile"

# Android emulator reaches the host machine via 10.0.2.2
$apiBase = if ($Device -eq "android") { "http://10.0.2.2:8000" } else { "http://localhost:8000" }

Push-Location $appDir
try {
    flutter run -d $Device --dart-define=API_BASE_URL=$apiBase
} finally {
    Pop-Location
}
