$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path .env)) { throw 'Run Setup.ps1 first.' }
$cfg = ConvertFrom-StringData (Get-Content .env -Raw)
$uri = "http://$($cfg.LAN_IP):10501"
Invoke-RestMethod "$uri/health"
$body = @{text='Guten Tag. Jarvis ist bereit. Die Solaranlage liefert heute Strom.'} | ConvertTo-Json -Compress
$timer = [Diagnostics.Stopwatch]::StartNew()
Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$uri/synthesize" -Headers @{'X-API-Key'=$cfg.JARVIS_TTS_TOKEN} -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -OutFile '.\qwen-test.wav' -TimeoutSec 120
$timer.Stop()
Write-Host ('Generation + transfer: {0:N2}s' -f $timer.Elapsed.TotalSeconds)
Invoke-Item '.\qwen-test.wav'
