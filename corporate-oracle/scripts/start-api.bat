@echo off
REM Venv em caminho curto (evita limite de path do Windows)
set VENV=C:\corporate-oracle\venv
set ROOT=%~dp0..
set BACKEND=%ROOT%\backend

if not exist "%VENV%\Scripts\python.exe" (
  echo Criando venv em C:\corporate-oracle\venv ...
  python -m venv C:\corporate-oracle\venv
  "%VENV%\Scripts\pip" install -r "%BACKEND%\requirements.txt"
)

cd /d "%BACKEND%"
set PYTHONPATH=%BACKEND%
"%VENV%\Scripts\uvicorn.exe" app.main:app --reload --host 127.0.0.1 --port 8000
