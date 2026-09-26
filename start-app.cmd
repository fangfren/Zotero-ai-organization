@echo off
setlocal

set "PYTHONDONTWRITEBYTECODE=1"
if not defined PORT set "PORT=5187"
set "URL=http://127.0.0.1:%PORT%"
set "NO_BROWSER=0"

if /I "%~1"=="--no-browser" set "NO_BROWSER=1"

call "%~dp0find-python.cmd"
if errorlevel 1 (
  pause
  exit /b 1
)

powershell -NoProfile -Command "try { $payload = Invoke-RestMethod -Uri '%URL%/api/state' -TimeoutSec 1; if ($payload.ok) { exit 0 } } catch {}; exit 1" >nul 2>&1
if errorlevel 1 (
  start "Zotero Research Workbench" /min "%PYTHON%" %PYTHON_ARGS% "%~dp0app_server.py" --port %PORT%

  powershell -NoProfile -Command "$deadline = (Get-Date).AddSeconds(20); do { try { $payload = Invoke-RestMethod -Uri '%URL%/api/state' -TimeoutSec 1; if ($payload.ok) { exit 0 } } catch {}; Start-Sleep -Milliseconds 250 } while ((Get-Date) -lt $deadline); exit 1" >nul 2>&1
  if errorlevel 1 (
    echo The workbench server did not start on port %PORT%.
    echo Run the following command for details:
    echo "%PYTHON%" %PYTHON_ARGS% "%~dp0app_server.py" --port %PORT%
    pause
    exit /b 1
  )
)

if "%NO_BROWSER%"=="0" start "" "%URL%"
exit /b 0

