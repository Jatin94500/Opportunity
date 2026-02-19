@echo off
setlocal
cd /d "%~dp0"

set "ROOT_DIR=%~dp0..\..\.."
set "APP_PY=%~dp0.venv\Scripts\python.exe"
set "ROOT_PY=%ROOT_DIR%\.venv\Scripts\python.exe"

if exist "%APP_PY%" (
  "%APP_PY%" -c "import PyQt5" >nul 2>nul
  if not errorlevel 1 goto run
)

if exist "%ROOT_PY%" (
  "%ROOT_PY%" -c "import PyQt5" >nul 2>nul
  if not errorlevel 1 (
    set "APP_PY=%ROOT_PY%"
    goto run
  )
)

set "APP_PY=python"

:run
"%APP_PY%" run_gui.py %*
