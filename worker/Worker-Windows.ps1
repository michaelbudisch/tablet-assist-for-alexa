# Windows TAFA GPU worker management - no API tokens.
[CmdletBinding()]
param([ValidateSet('Prepare','Install','Start','Restart','Info')][string]$Action='Prepare')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$EnvFile=Join-Path $PSScriptRoot '.env'
$Report=Join-Path $PSScriptRoot 'GPU-Worker-Verbindungsdaten.txt'
function Get-Settings {
  $result=@{}
  if(Test-Path -LiteralPath $EnvFile) {
    foreach($line in (Get-Content -LiteralPath $EnvFile -Encoding UTF8)) {
      if($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$'){
        $result[$Matches[1]]=$Matches[2].Trim()
      }
    }
  }
  return $result
}
function Private-IP([string]$text) {
  $addr=$null
  if(-not [Net.IPAddress]::TryParse($text,[ref]$addr)){return $false}
  return ($addr.AddressFamily -eq [Net.Sockets.AddressFamily]::InterNetwork -and
      $text -match '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)')
}
function Ensure-Env {
  if(Test-Path -LiteralPath $EnvFile) {
    Write-Host 'Vorhandene .env bleibt unveraendert.' -ForegroundColor Green
    return
  }
  $addresses=@(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    (Private-IP $_.IPAddress) -and $_.AddressState -eq 'Preferred'
  } | Select-Object -ExpandProperty IPAddress -Unique)
  if(-not $addresses.Count){throw 'Keine private LAN-IP gefunden.'}
  Write-Host ('Gefundene LAN-Adressen: '+($addresses -join ', '))
  $ip=$addresses[0]
  if($addresses.Count -gt 1){
    $reply=Read-Host ('Gewuenschte LAN-IP (Enter fuer '+$ip+')')
    if($reply){$ip=$reply.Trim()}
  }
  if($addresses -notcontains $ip){throw 'IP ist diesem Rechner nicht zugewiesen.'}
  $settings=@(
    ('LAN_IP='+$ip),
    'QWEN_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice',
    'QWEN_SPEAKER=Ryan',
    'STREAM_VOICE_MODE=fast',
    'STREAM_FIXED_MODEL_SIZE=1.7B',
    'STREAM_VOICE_VARIANT=1',
    'STREAM_TEXT_CLEANUP=1',
    'STREAM_SPEECH_SPLIT=0'
  )
  [IO.File]::WriteAllLines($EnvFile,[string[]]$settings,(New-Object Text.UTF8Encoding($false)))
  Write-Host 'Neue .env OHNE Token erstellt.' -ForegroundColor Green
}
function Check-Docker {
  if(-not (Get-Command docker -ErrorAction SilentlyContinue)){throw 'Docker Desktop fehlt.'}
  & docker info --format '{{.OSType}}' | Out-Null
  if($LASTEXITCODE -ne 0){throw 'Docker Desktop starten.'}
  & docker compose version | Out-Null
  if($LASTEXITCODE -ne 0){throw 'Docker Compose fehlt.'}
}
function Compose([string[]]$Arguments) {
  & docker compose @Arguments
  if($LASTEXITCODE -ne 0){throw 'Docker Compose fehlgeschlagen. Obige Ausgabe beachten.'}
}
function Write-Report {
  $settings=Get-Settings
  $ip=[string]$settings['LAN_IP']
  if(-not (Private-IP $ip)){throw 'LAN_IP in .env ist keine private IPv4.'}
  $lines=@(
    'TAFA GPU WORKER - VERBINDUNGSDATEN (ohne Zugangsdaten)',
    '=====================================================',
    ('Erstellt: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
    ('GPU-PC: '+$ip),
    '',
    'Nur wenn der jeweilige Compose-Dienst gestartet ist:',
    ('GPU Whisper Wyoming: '+$ip+':10300'),
    ('Qwen Streaming TTS: http://'+$ip+':10502'),
    ('Qwen TTS legacy (optional): http://'+$ip+':10501'),
    ('Vision (optional): http://'+$ip+':10503'),
    ('Diagnose (optional): http://'+$ip+':10504'),
    ('Ollama Gateway (optional): http://'+$ip+':11434'),
    '',
    'HOME ASSISTANT: Einstellungen > Geraete & Dienste > TAFA > Optionen',
    '  Abschnitt: Sprachserver & GPU',
    ('  GPU-Adresse: http://'+$ip+':10502'),
    '  Routing: Automatisch -> Qwen (online), Piper (offline)',
    '  Assist TTS: Tablet Assist Stream',
    '',
    'Keine API-Tokens erforderlich.',
    'SICHERHEIT: Nur im vertrauenswuerdigen LAN verwenden!',
    'Keine Portfreigabe, keine Cloudfreigabe, kein Gast-WLAN.',
    'Windows Firewall auf notwendige HA-/Sprachserver-Adressen einschraenken.',
    '',
    'CPU-PIPER (5000), MP3-Generator (5001), Audio (8080)',
    'laufen bei externem Betrieb auf dem Proxmox-Sprachserver.',
    ''
  )
  [IO.File]::WriteAllLines($Report,[string[]]$lines,(New-Object Text.UTF8Encoding($false)))
  Write-Host ('Verbindungsliste: '+$Report) -ForegroundColor Cyan
}
try {
  Ensure-Env
  switch($Action) {
    'Prepare' { Write-Host 'Konfiguration erstellt; optional 01-Installieren.bat starten.' }
    'Install' {
      Check-Docker
      Compose -Arguments @('--profile','stream','config','--quiet')
      Compose -Arguments @('--profile','stream','up','-d','--build','whisper','qwen-stream')
    }
    'Start' {
      Check-Docker
      Compose -Arguments @('--profile','stream','up','-d','whisper','qwen-stream')
    }
    'Restart' {
      Check-Docker
      $running=@(& docker compose --profile '*' ps --status running --services)
      if($LASTEXITCODE -ne 0){throw 'Dockerstatus nicht lesbar.'}
      $services=@($running | ForEach-Object {$_.Trim()} | Where-Object {$_})
      if($services.Count -gt 0){
        Compose (@('--profile','*','restart') + $services)
      }else{
        Compose -Arguments @('--profile','stream','up','-d','whisper','qwen-stream')
      }
    }
    'Info' { Write-Host 'Aktualisiere Verbindungsdaten.' }
  }
  Write-Report
  Write-Host 'Fertig.' -ForegroundColor Green
  exit 0
}catch{
  Write-Host ('FEHLER: '+$_.Exception.Message) -ForegroundColor Red
  exit 1
}
