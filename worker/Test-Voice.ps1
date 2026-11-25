$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path .env)) { throw 'Use the existing private .env file.' }
$cfg = @{}
Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { $cfg[$matches[1]] = $matches[2] } }
if (-not $cfg['LAN_IP']) { throw 'Missing settings' }
$body = @{text='Guten Tag. Alle Systeme sind bereit. Die aktuelle Energieversorgung liegt im vorgesehenen Bereich. Wie kann ich Ihnen behilflich sein?'} | ConvertTo-Json -Compress
$body | Set-Content -Encoding ASCII .voice-test.json
try {
  $url = "http://$($cfg['LAN_IP']):10502"
  Invoke-RestMethod "$url/health" -TimeoutSec 5 | Format-List
  curl.exe --silent --show-error --fail --max-time 90 -H 'Content-Type: application/json' --data-binary '@.voice-test.json' -o voice-test.wav -w "Gesamt: %{time_total}s\n" "$url/synthesize"
  if ($LASTEXITCODE -ne 0) { throw 'Voice test failed' }
  $player = New-Object System.Media.SoundPlayer (Join-Path $PSScriptRoot 'voice-test.wav')
  try { $player.PlaySync() } finally { $player.Dispose() }
} finally { Remove-Item .voice-test.json -ErrorAction SilentlyContinue }
