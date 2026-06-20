@echo off
set VENV=C:\corporate-oracle\venv
set ROOT=%~dp0..
set BACKEND=%ROOT%\backend

if not exist "%VENV%\Scripts\python.exe" (
  echo Execute start-api.bat primeiro para criar o venv.
  exit /b 1
)

cd /d "%BACKEND%"
set PYTHONPATH=%BACKEND%
"%VENV%\Scripts\python.exe" -m app.cli.index %*
