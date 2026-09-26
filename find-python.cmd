@echo off
rem Locate a compatible Python interpreter and set:
rem   PYTHON      executable name or absolute path
rem   PYTHON_ARGS optional launcher arguments, such as -3

set "PYTHON="
set "PYTHON_ARGS="

if defined RESEARCH_WORKBENCH_PYTHON (
  if exist "%RESEARCH_WORKBENCH_PYTHON%" (
    set "PYTHON=%RESEARCH_WORKBENCH_PYTHON%"
    call :is_compatible
    if not errorlevel 1 exit /b 0
    echo RESEARCH_WORKBENCH_PYTHON is not Python 3.10 or newer:
    echo %RESEARCH_WORKBENCH_PYTHON%
    exit /b 1
  )
  where "%RESEARCH_WORKBENCH_PYTHON%" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON=%RESEARCH_WORKBENCH_PYTHON%"
    call :is_compatible
    if not errorlevel 1 exit /b 0
    echo RESEARCH_WORKBENCH_PYTHON is not Python 3.10 or newer:
    echo %RESEARCH_WORKBENCH_PYTHON%
    exit /b 1
  )
  echo RESEARCH_WORKBENCH_PYTHON points to an executable that was not found:
  echo %RESEARCH_WORKBENCH_PYTHON%
  exit /b 1
)

if exist "%~dp0.venv\Scripts\python.exe" (
  set "PYTHON=%~dp0.venv\Scripts\python.exe"
  call :is_compatible
  if not errorlevel 1 exit /b 0
)

set "PYTHON=python"
call :is_compatible
if not errorlevel 1 exit /b 0

set "PYTHON=py"
set "PYTHON_ARGS=-3"
call :is_compatible
if not errorlevel 1 exit /b 0

echo Python 3.10 or newer was not found.
echo Install Python from https://www.python.org/downloads/ and enable "Add Python to PATH".
echo You can also set RESEARCH_WORKBENCH_PYTHON to the full path of python.exe.
exit /b 1

:is_compatible
"%PYTHON%" %PYTHON_ARGS% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
exit /b %ERRORLEVEL%
