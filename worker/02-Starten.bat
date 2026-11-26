@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\Worker-Windows.ps1" -Action Start
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo FEHLER: Siehe oben.
pause
exit /b %RC%
