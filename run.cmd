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

"%PYTHON%" "%~dp0sync_zotero.py" %*
set "EXITCODE=%ERRORLEVEL%"

echo.
echo Output: %~dp0output
echo Dashboard: %~dp0output\dashboard\index.html
pause
exit /b %EXITCODE%
