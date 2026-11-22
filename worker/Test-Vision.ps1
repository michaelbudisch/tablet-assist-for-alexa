param(
    [Parameter(Mandatory=$true)][string]$ImagePath,
    [ValidateSet('scene','objects','object_in_hand')][string]$Mode = 'scene',
    [ValidateSet('qwen3-vl:2b-instruct','qwen3-vl:4b-instruct','qwen3-vl:8b-instruct','gemma3:4b')][string]$Model
)
$ErrorActionPreference = 'Stop'
$image = Get-Item -LiteralPath $ImagePath
if ($image.Length -gt 2097152 -or $image.Extension -notin '.jpg','.jpeg','.png') {
    throw 'Use a consented non-private JPEG or PNG up to 2 MiB.'
}
Set-Location $PSScriptRoot
if (-not (Test-Path .env)) { throw 'Use the existing private .env file.' }
$cfg = @{}
Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { $cfg[$matches[1]] = $matches[2] } }
if (-not $cfg['JARVIS_TTS_TOKEN'] -or -not $cfg['LAN_IP']) { throw 'Missing settings' }
$headers = @{'X-API-Key'=$cfg['JARVIS_TTS_TOKEN']}
$base = "http://$($cfg['LAN_IP']):10503"
Invoke-RestMethod -Uri "$base/health" -Headers $headers -TimeoutSec 15 | ConvertTo-Json
$body = @{image=[Convert]::ToBase64String([IO.File]::ReadAllBytes($image.FullName));mode=$Mode}
if ($Model) { $body.model = $Model }
Invoke-RestMethod -Uri "$base/describe" -Headers $headers -Method Post -ContentType 'application/json' -Body ($body | ConvertTo-Json -Compress) -TimeoutSec 125 | ConvertTo-Json
