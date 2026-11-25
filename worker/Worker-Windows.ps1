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
    'TAFA GPU WORKER 2.2.2 - VERBINDUNGSDATEN + EINRICHTUNG (DE / EN)',
    '================================================================',
    ('Erstellt / Generated: '+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
    ('GPU-PC LAN_IP (aus .env): '+$ip),
    '',
    'DEUTSCH - SCHRITT FUER SCHRITT',
    '==============================',
    'WICHTIG: Die folgenden Dienste sind nur erreichbar, wenn die betreffenden',
    'Docker-Compose-Container laufen. Dies ist KEINE Live-Funktionspruefung.',
    '',
    '1) GPU-DIENSTE UND ADRESSEN',
    ('  Whisper GPU / Wyoming TCP: Host '+$ip+' | Port 10300'),
    ('  Qwen Streaming / TTS:      http://'+$ip+':10502'),
    ('  Ollama / Text-KI optional: http://'+$ip+':11434'),
    ('  Qwen Legacy TTS optional:  http://'+$ip+':10501'),
    ('  Vision optional:           http://'+$ip+':10503'),
    ('  Diagnose optional:         http://'+$ip+':10504'),
    '  Unterscheidung: 10300=Spracherkennung, 10502=Sprachausgabe,',
    '                  11434=KI-Antworten; das sind drei getrennte Dienste.',
    '',
    '2) HOME ASSISTANT - ZUERST WYOMING INTEGRIEREN (GPU-WHISPER)',
    '  Einstellungen > Geraete & Dienste > Integration hinzufuegen',
    '  > Wyoming Protocol (nicht Ollama / nicht TAFA).',
    ('  Wyoming Host: '+$ip+'    Wyoming Port: 10300'),
    '  Home Assistant legt daraufhin eine stt.*-Entitaet an.',
    '  Die tatsaechliche Entitaets-ID unter Geraete & Dienste > Entitaeten',
    '  oder Entwicklerwerkzeuge > Zustaende nachsehen und kopieren.',
    '  Diese Entitaets-ID wird spaeter als gpu_stt in TAFA eingetragen!',
    '  Hinweis: Nur die IP in TAFA einzutragen aktiviert GPU-Whisper NICHT.',
    '  Wichtig: Wyoming Port 10300 muss auch von HOME ASSISTANT erreichbar sein.',
    '',
    '  CPU-FALLBACK (PROXMOX): Eine zweite Wyoming-Integration fuer den',
    '  CPU-Sprachserver hinzufuegen: Host=<PROXMOX-SPRACHSERVER-IP>, Port=10300.',
    '  Die von HA erzeugte CPU-stt.*-Entitaet wird in TAFA zu cpu_stt.',
    '  Bei nur EINER Wyoming-STT-Entitaet ist Autoauswahl moeglich;',
    '  mit CPU + GPU unbedingt beide unterschiedlichen IDs explizit waehlen.',
    '',
    '3) HOME ASSISTANT - OLLAMA FUER KI-GESPRAECHE EINRICHTEN',
    '  Ollama ist NICHT identisch mit Qwen-Streaming-TTS.',
    '  Falls Ollama noch nicht laeuft, auf dem GPU-PC (optional):',
    '    docker compose --profile llm up -d ollama ollama-gateway',
    '  Das benoetigte Textmodell muss bereits installiert sein;',
    '  z. B. qwen3:4b-instruct (Installation optional per:',
    '    docker compose exec ollama ollama pull qwen3:4b-instruct',
    '  ). Nicht ungefragt grosse Modelle laden.',
    '  In HOME ASSISTANT > Einstellungen > Geraete & Dienste',
    '    > Integration hinzufuegen > Ollama.',
    ('  Ollama Server/URL: http://'+$ip+':11434'),
    '  Unter Ollama einen Konversationsagenten hinzufuegen und',
    '  ein installiertes TEXT-Modell (z. B. qwen3:4b-instruct) auswaehlen.',
    '  Anschliessend die echte conversation.*-Entitaets-ID in HA ablesen,',
    '  z. B. conversation.ollama_conversation. NICHT den Geraetenamen raten.',
    '  In TAFA wird diese Entitaets-ID bei llm_agent eingetragen.',
    '  Ohne Ollama funktionieren Whisper + TTS, aber freie KI-Fragen nicht.',
    '',
    '4) TAFA APP - EXAKTE FELDER',
    '  HOME ASSISTANT > Einstellungen > Apps > TAFA > Konfiguration',
    '  (bei App-Installation; nicht den alten Integrations-Optionsdialog).',
    '  speech_mode          = external     [wenn Proxmox CPU-Piper nutzt]',
    '  external_piper_base  = http://<PROXMOX-SPRACHSERVER-IP>:5000',
    '  cpu_stt              = <CPU-WYOMING-STT-ENTITAETS-ID AUS HA>',
    '  gpu_base             = http://'+$ip+':10502',
    '  gpu_stt              = <GPU-WYOMING-STT-ENTITAETS-ID AUS HA>',
    '  gpu_stt_host         = '+$ip,
    '  hardware_profile     = automatic',
    '  llm_agent            = <OLLAMA-CONVERSATION-ENTITAETS-ID AUS HA>',
    '  WICHTIG: gpu_base ist TTS; gpu_stt ist eine stt.*-ENTITAET, KEINE URL.',
    '  gpu_stt_host ist NUR die IP, ohne http:// und ohne :10300.',
    '  cpu_stt / gpu_stt sind verschieden. Keine API-Tokens eintragen.',
    '  Fuer TAFA-internes CPU-Whisper: speech_mode=local,',
    '  external_piper_base entfaellt. Bestehende Einstellungen bewahren.',
    '',
    '5) ASSIST-PIPELINE IN HOME ASSISTANT PRUEFEN',
    '  Einstellungen > Sprachassistenten > Pipeline "TAFA Lokal".',
    '  STT = Tablet Assist Sprachrouter   [Waehlt GPU, CPU-Fallback]',
    '  Gespraech = Tablet Assist Gespraechsrouter [nutzt llm_agent]',
    '  TTS = Tablet Assist Stream         [Waehlt Qwen, Piper-Fallback]',
    '  Bestehende Assist-Pipelines nicht blind ersetzen.',
    '  TAFA App nach Konfigurationsaenderung neu starten;',
    '  nach einem Integration-Update HA Core einmal neu starten.',
    '  Android Device Bridge 1.0.1+: Native Sprachunterhaltung optional',
    '  unter Rufwort aktivieren; derselbe HA-Benutzer wie im Audi Raum.',
    '',
    '6) PRUEFEN, OB GPU-WHISPER WIRKLICH VERWENDET WIRD',
    '  Eine Frage am Tablet sprechen. Unter Entwicklerwerkzeuge > Zustaende',
    '  die stt.*-Entitaet "Tablet Assist Sprachrouter" pruefen:',
    '    letztes_backend = zusatzrechner  -> GPU-Whisper',
    '    letztes_backend = homeserver     -> CPU/Fallback',
    '    fallback = Anzahl CPU-Rueckfaelle',
    '    letzte_dauer_ms = Zeit inkl. Audioempfang / STT',
    '  Bei homeserver: gpu_stt, Wyoming-Port 10300 und Pipeline pruefen.',
    '  Bei langsamer Reaktion zusaetzlich Android-Sprechpause kontrollieren',
    '  (Standard ca. 1700 ms). Ollama-Antwortzeit ist separat.',
    '',
    '7) SICHERHEIT UND OPTIONALE PORTS',
    '  CPU Piper 5000, MP3-Generator 5001 und Audio 8080 laufen bei',
    '  externem Betrieb auf dem Proxmox-Sprachserver, NICHT auf diesem PC.',
    '  Alle Ports nur im privaten LAN / HA und Sprachserver freigeben.',
    '  KEINE Router-Portweiterleitung, KEINE Cloudfreigabe, KEIN Gast-WLAN.',
    '  HTTP ist unverschluesselt; Windows-Firewall eng beschraenken.',
    '  Dieser Bericht enthaelt keine Zugangsdaten oder Tokens, aber LAN-IPs.',
    '',
    '----------------------------------------------------------------',
    '',
    'ENGLISH - FIRST RUN CHECKLIST',
    '=============================',
    'Endpoints below require the respective Docker Compose service to run.',
    'This file does not test service availability.',
    '',
    '1) GPU COMPUTER ENDPOINTS',
    ('  GPU Whisper / Wyoming TCP: host '+$ip+' | port 10300'),
    ('  Qwen streaming TTS:       http://'+$ip+':10502'),
    ('  Ollama text LLM (opt.):   http://'+$ip+':11434'),
    ('  Legacy Qwen TTS (opt.):   http://'+$ip+':10501'),
    ('  Vision (opt.):            http://'+$ip+':10503'),
    ('  Diagnostics (opt.):       http://'+$ip+':10504'),
    '  10300 is speech recognition; 10502 speech output; 11434 text AI.',
    '',
    '2) INSTALL HOME ASSISTANT WYOMING PROTOCOL (GPU WHISPER)',
    '  Settings > Devices & services > Add integration > Wyoming Protocol.',
    ('  Host = '+$ip+'    Port = 10300'),
    '  Find the actual new stt.* entity under Entities / Developer tools > States.',
    '  In the TAFA App set gpu_stt to THAT ENTITY ID (not an IP or URL).',
    '  For CPU fallback also add Wyoming Protocol for the Proxmox speech',
    '  server: host=<PROXMOX-SPEECH-SERVER-IP>, port=10300. Use its',
    '  actual CPU stt.* entity in cpu_stt; these IDs must differ.',
    '  A single Wyoming STT can be auto-selected; with two, select both.',
    '',
    '3) INSTALL HOME ASSISTANT OLLAMA FOR OPEN-ENDED AI QUESTIONS',
    '  Optional start from the GPU worker folder:',
    '    docker compose --profile llm up -d ollama ollama-gateway',
    '  Install/check an Ollama text model (e.g. qwen3:4b-instruct) separately.',
    '  Settings > Devices & services > Add integration > Ollama.',
    ('  Ollama server URL = http://'+$ip+':11434'),
    '  Add an Ollama conversation agent, select an INSTALLED text model.',
    '  Copy the actual conversation.* entity ID from Home Assistant into',
    '  TAFA llm_agent; do not assume the device name is the entity ID.',
    '  Without Ollama, STT/TTS still work but free AI questions do not.',
    '',
    '4) TAFA APP - SETTINGS > APPS > TAFA > CONFIGURATION',
    '  speech_mode          = external (if using Proxmox CPU Piper)',
    '  external_piper_base  = http://<PROXMOX-SPEECH-SERVER-IP>:5000',
    '  cpu_stt              = <CPU WYOMING STT ENTITY ID>',
    ('  gpu_base             = http://'+$ip+':10502'),
    '  gpu_stt              = <GPU WYOMING STT ENTITY ID>',
    ('  gpu_stt_host         = '+$ip),
    '  hardware_profile     = automatic',
    '  llm_agent            = <OLLAMA CONVERSATION ENTITY ID>',
    '  gpu_base is TTS; gpu_stt requires a Wyoming entity; gpu_stt_host is',
    '  only the GPU host IP (no protocol and no port). No worker API tokens.',
    '  In local TAFA CPU mode, use speech_mode=local, not external Piper.',
    '',
    '5) HOME ASSISTANT ASSIST PIPELINE: "TAFA Lokal"',
    '  STT = Tablet Assist Sprachrouter (GPU with CPU fallback)',
    '  Conversation = Tablet Assist Gespraechsrouter (routes to llm_agent)',
    '  TTS = Tablet Assist Stream (Qwen with Piper fallback)',
    '  Preserve existing user pipelines. Restart TAFA App after settings;',
    '  after an integration update also restart Home Assistant Core once.',
    '  Optional native Android voice: enable Native voice conversation in',
    '  Device Bridge 1.0.1+ with the matching HA room user account.',
    '',
    '6) VERIFY GPU RECOGNITION',
    '  Ask a question, then inspect "Tablet Assist Sprachrouter" stt.* state:',
    '  letztes_backend=zusatzrechner means GPU; homeserver means CPU/fallback.',
    '  letzte_dauer_ms includes audio capture/transmission and STT time.',
    '  Android speech-end pause and Ollama answer latency are separate.',
    '',
    '7) LAN SAFETY',
    '  External CPU Piper (5000), MP3 generator (5001) and audio (8080)',
    '  run on the PROXMOX speech server, not on the GPU computer.',
    '  Use trusted private LAN only; restrict Windows firewall to the HA',
    '  and Proxmox source IPs. Never forward these ports to the Internet.',
    '  HTTP has no encryption. Report contains LAN IPs but no credentials.',
    ''
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
  Write-Host 'Fertig.' -ForegroundColor Green
  exit 0
}catch{
  Write-Host ('FEHLER: '+$_.Exception.Message) -ForegroundColor Red
  exit 1
}
