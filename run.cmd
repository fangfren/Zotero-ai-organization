@echo off
setlocal

set "PYTHONDONTWRITEBYTECODE=1"

call "%~dp0find-python.cmd"
if errorlevel 1 (
  pause
  exit /b 1
)

"%PYTHON%" %PYTHON_ARGS% "%~dp0sync_zotero.py" %*
set "EXITCODE=%ERRORLEVEL%"

echo.
echo Output: %~dp0output
echo Dashboard: %~dp0output\dashboard\index.html
pause
exit /b %EXITCODE%
