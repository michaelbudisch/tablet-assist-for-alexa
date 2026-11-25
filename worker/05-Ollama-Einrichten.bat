@echo off
setlocal
cd /d "%~dp0"
echo Ollama wird auf dem lokalen GPU-PC gestartet.
docker compose --profile llm up -d ollama ollama-gateway
if errorlevel 1 (
  echo FEHLER: Ollama konnte nicht gestartet werden.
  pause
  exit /b 1
)
echo Optionaler Textmodell-Download: qwen3:4b-instruct
choice /c JN /n /m "Modell herunterladen? Groesserer Download [J/N]: "
if errorlevel 2 goto report
docker compose --profile llm exec -T ollama ollama pull qwen3:4b-instruct
if errorlevel 1 (
  echo FEHLER: Modelldownload fehlgeschlagen.
  pause
  exit /b 1
)
:report
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Worker-Windows.ps1" -Action Info
pause
exit /b %ERRORLEVEL%
