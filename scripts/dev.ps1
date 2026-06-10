# Start backend and frontend in development mode (requires Slither + solc locally)
$root = Split-Path -Parent $PSScriptRoot

Write-Host "Starting backend on :8000 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; `$env:PYTHONPATH='.'; .\.venv\Scripts\uvicorn app.main:app --reload --port 8000 --app-dir ."

Write-Host "Starting frontend on :5173 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host "Open http://localhost:5173"
