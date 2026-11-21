$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (Test-Path .env) { Write-Host '.env already exists. Keeping existing configuration.'; exit 0 }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Install and start Docker Desktop first.' }
docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker is not running.' }
Write-Host 'Choose the IPv4 address of this PC on your private home LAN:'
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | Format-Table IPAddress,InterfaceAlias
$ip = Read-Host 'LAN IPv4 of this PC'
$parsed = $null
if (-not [Net.IPAddress]::TryParse($ip,[ref]$parsed) -or $parsed.AddressFamily -ne 'InterNetwork' -or $ip -notmatch '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)') { throw 'Use a private IPv4 address.' }
if (-not (Get-NetIPAddress -AddressFamily IPv4 -IPAddress $ip -ErrorAction SilentlyContinue)) { throw 'This IP is not assigned to this PC.' }
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes); $rng.Dispose()
$token = [BitConverter]::ToString($bytes).Replace('-','').ToLowerInvariant()
@("LAN_IP=$ip", "JARVIS_TTS_TOKEN=$token", "QWEN_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice", "QWEN_SPEAKER=Ryan") | Set-Content -Path .env -Encoding ASCII
Write-Host 'Configuration saved. Keep .env private. No firewall rules were changed.'
Write-Host 'Next: docker compose up -d --build whisper'
