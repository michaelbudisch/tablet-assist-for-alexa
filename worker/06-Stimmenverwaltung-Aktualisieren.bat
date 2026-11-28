@echo off
setlocal
cd /d "%~dp0"
if not exist ".env" (
  echo FEHLER: .env fehlt. Bitte zuerst 00-Konfiguration.bat ausfuehren.
  pause
  exit /b 2
)
findstr /b /i "STREAM_VOICE_MODE=fixed" ".env" >nul
if errorlevel 1 (
  echo Stimmenvarianten benoetigen STREAM_VOICE_MODE=fixed in der .env.
  echo Bitte diese Einstellung pruefen und erneut ausfuehren.
  pause
  exit /b 2
)
echo TAFA Stimmenverwaltung wird aktualisiert. Andere GPU-Dienste bleiben unveraendert.
docker compose --profile stream up -d --build --no-deps qwen-stream
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo FEHLER: GPU-Worker aktualisieren fehlgeschlagen.
if "%RC%"=="0" echo OK: Qwen-Stream aktualisiert. Die Stimmen koennen nun in TAFA erstellt werden.
pause
exit /b %RC%
