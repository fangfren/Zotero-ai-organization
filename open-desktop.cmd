@echo off
setlocal

set "URL=http://127.0.0.1:5187"
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

call "%~dp0start-app.cmd" --no-browser
if errorlevel 1 exit /b 1

if exist "%EDGE%" (
  start "" "%EDGE%" --app=%URL% --window-size=1320,860
) else (
  start "" "%URL%"
)

