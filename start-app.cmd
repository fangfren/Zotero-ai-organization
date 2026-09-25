@echo off
setlocal

set "PYTHONDONTWRITEBYTECODE=1"

set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not exist "%PYTHON%" (
  echo Bundled Python was not found:
  echo %PYTHON%
  pause
  exit /b 1
)

start "Zotero 研究工作台" "%PYTHON%" "%~dp0app_server.py"
timeout /t 1 /nobreak >nul
start "" "http://127.0.0.1:5187"

