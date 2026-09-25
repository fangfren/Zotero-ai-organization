@echo off
setlocal

set "PYTHONDONTWRITEBYTECODE=1"

set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "URL=http://127.0.0.1:5187"
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

if not exist "%PYTHON%" (
  echo Bundled Python was not found:
  echo %PYTHON%
  pause
  exit /b 1
)

powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing -Uri '%URL%' -TimeoutSec 2).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  start "Zotero 研究工作台" "%PYTHON%" "%~dp0app_server.py"
  timeout /t 2 /nobreak >nul
)

if exist "%EDGE%" (
  start "" "%EDGE%" --app=%URL% --window-size=1320,860
) else (
  start "" "%URL%"
)

