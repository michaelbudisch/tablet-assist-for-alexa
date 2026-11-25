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
  # This report is guidance, not a live Docker or Home Assistant status check.
  # All endpoints are taken from the selected LAN_IP, never hard-coded to one user.
  # Keep script messages ASCII so the script also works with Windows PowerShell 5.1.
  $lines=@(
    'TAFA GPU WORKER 2.2.3 - ADRESSEN / ENDPOINTS',
    '==========================================',
    ('GPU-PC IP / LAN IP: '+$ip),
    '',
    'DEUTSCH - WO EINTRAGEN?',
    '',
    'GPU-WHISPER (Sprache erkennen)',
    ('  Home Assistant > Geraete & Dienste > Wyoming Protocol: Host '+$ip+' | Port 10300'),
    ('  TAFA > Benutzeroberflaeche > Einstellungen > GPU-Whisper-IP (gpu_stt_host): '+$ip),
    '  TAFA > GPU-Whisper (gpu_stt): die in HA angelegte stt.*-Entitaet waehlen',
    '',
    'QWEN (Sprache ausgeben)',
    ('  TAFA > Benutzeroberflaeche > Einstellungen > Qwen (gpu_base): http://'+$ip+':10502'),
    '',
    'OLLAMA (KI-Gespraeche, optional)',
    ('  Home Assistant > Geraete & Dienste > Ollama > Server-URL: http://'+$ip+':11434'),
    '  TAFA > Text-KI (llm_agent): die in HA angelegte conversation.*-Entitaet waehlen',
    '',
    'ENGLISH - WHERE TO ENTER?',
    '',
    'GPU WHISPER (speech recognition)',
    ('  Home Assistant > Devices & services > Wyoming Protocol: Host '+$ip+' | Port 10300'),
    ('  TAFA > Control Center > Settings > GPU Whisper IP (gpu_stt_host): '+$ip),
    '  TAFA > GPU Whisper (gpu_stt): select the stt.* entity created in HA',
    '',
    'QWEN (speech output)',
    ('  TAFA > Control Center > Settings > Qwen (gpu_base): http://'+$ip+':10502'),
    '',
    'OLLAMA (text AI, optional)',
    ('  Home Assistant > Devices & services > Ollama > Server URL: http://'+$ip+':11434'),
    '  TAFA > Text AI (llm_agent): select the conversation.* entity created in HA',
    '',
    'Nur die GPU-PC-Adressen aus .env / Only addresses of this GPU PC.',
    'Proxmox-Piper/MP3-Adressen sind nicht in dieser Datei bekannt.',
    'Proxmox Piper/MP3 addresses are not known to this GPU worker.'
  )
  [IO.File]::WriteAllLines($Report,[string[]]$lines,(New-Object Text.UTF8Encoding($false)))
  Write-Host ('Verbindungsliste / connection guide: '+$Report) -ForegroundColor Cyan
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
  if($Action -in @('Prepare','Install','Start')){
    Write-Host '04-Verbindungsdaten.bat zeigt nur IP-Endpunkte und Eintragungsorte.' -ForegroundColor Cyan
  }
  Write-Host 'Fertig.' -ForegroundColor Green
  exit 0
}catch{
  Write-Host ('FEHLER: '+$_.Exception.Message) -ForegroundColor Red
  exit 1
}
