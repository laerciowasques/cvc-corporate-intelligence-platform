@echo off
REM Serve o HTML localmente (evita bloqueio CORS do file://)
cd /d "%~dp0.."
echo Abrindo plataforma em http://127.0.0.1:5500/CVC_Corporate_Intelligence_Platform.html
echo Certifique-se de que a API esta rodando: scripts\start-api.bat
python -m http.server 5500 --bind 127.0.0.1
