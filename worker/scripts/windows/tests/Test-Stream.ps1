$ErrorActionPreference = 'Stop'
$WorkerRoot=Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
Set-Location -LiteralPath $WorkerRoot
if (-not (Test-Path .env)) { throw 'Use the existing private .env file.' }
$cfg = @{}
Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { $cfg[$matches[1]] = $matches[2] } }
if (-not $cfg['LAN_IP']) { throw 'Missing settings' }
$body = @{text='Die Sprachausgabe funktioniert. Ich kann jetzt sprechen, waehrend der Rest der Antwort erzeugt wird.'} | ConvertTo-Json -Compress
$body | Set-Content -Encoding ASCII .stream-test.json
try {
  curl.exe --silent --show-error --fail --max-time 90 -H 'Content-Type: application/json' --data-binary '@.stream-test.json' -o test-stream.pcm -w "Erste Bytes: %{time_starttransfer}s | Gesamt: %{time_total}s`n" "http://$($cfg['LAN_IP']):10502/stream"
  if ($LASTEXITCODE -ne 0) { throw 'Stream test failed' }
  Write-Host 'PCM stream received. See Docker logs for model time to first playable audio.'
} finally { Remove-Item .stream-test.json -ErrorAction SilentlyContinue }
