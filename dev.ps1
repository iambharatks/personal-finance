# Runs the app on this PC: API on http://127.0.0.1:8000, UI on http://localhost:5173
# Usage:  .\dev.ps1      (Ctrl+C stops both)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Push-Location "$root\server"
uv run python -m app.cli migrate
# "python -m uvicorn", not the uvicorn.exe shim: Windows app control blocks that shim here.
$api = Start-Process uv -NoNewWindow -PassThru `
    -ArgumentList "run", "python", "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"
Pop-Location

try {
    Push-Location "$root\client"
    if (-not (Test-Path node_modules)) { npm install }
    npm run dev
}
finally {
    Pop-Location
    # /T also stops the Python process that uv started.
    taskkill /PID $api.Id /T /F | Out-Null
}
