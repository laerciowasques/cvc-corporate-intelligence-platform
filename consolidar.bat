@echo off
REM Regenera o HTML portátil (base64 seguro)
cd /d "%~dp0"
python repair_html.py 2>nul
if errorlevel 1 python consolidate_platform.py
if errorlevel 1 (
  echo Falha. Tentando reparo completo...
  python repair_html.py
)
echo.
echo Pronto: CVC_Corporate_Intelligence_Platform.html
pause
