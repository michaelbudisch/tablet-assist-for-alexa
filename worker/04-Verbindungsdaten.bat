@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Worker-Windows.ps1" -Action Info
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo FEHLER: Siehe oben.
if "%RC%"=="0" start "" notepad.exe "%~dp0GPU-Worker-Verbindungsdaten.txt"
pause
exit /b %RC%
