# Windows TAFA GPU worker management - no API tokens.
[CmdletBinding()]
param([ValidateSet('Prepare','Install','Start','Restart','Info','Ollama')][string]$Action='Prepare')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkerRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $WorkerRoot
$EnvFile=Join-Path $WorkerRoot '.env'
$Report=Join-Path $WorkerRoot 'tafa-worker.json'
$TextReport=Join-Path $WorkerRoot 'GPU-Worker-Verbindungsdaten.txt'
$WorkerIdFile=Join-Path $WorkerRoot '.tafa-worker-id'
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
function Ask-YesNo([string]$Question) {
  $reply=Read-Host ($Question+' [j/N]')
  return ($reply.Trim() -match '^(?i:j|ja|y|yes)$')
}
function Setup-Ollama {
  Check-Docker
  Compose -Arguments @('--profile','llm','up','-d','ollama','ollama-gateway')
  Write-Host 'Ollama ist gestartet. Ein Textmodell wird nur nach Zustimmung heruntergeladen.'
  if(Ask-YesNo 'Textmodell qwen3:4b-instruct herunterladen? (groesserer Download)') {
    & docker compose --profile llm exec -T ollama ollama pull qwen3:4b-instruct
    if($LASTEXITCODE -ne 0){throw 'Ollama-Modelldownload fehlgeschlagen.'}
  }
}
function Write-Report {
  $settings=Get-Settings
  $ip=[string]$settings['LAN_IP']
  if(-not (Private-IP $ip)){throw 'LAN_IP in .env ist keine private IPv4.'}
  # Keep the worker identity across IP changes, without using an API token.
  $workerId=''
  if(Test-Path -LiteralPath $WorkerIdFile){
    $workerId=([string](Get-Content -LiteralPath $WorkerIdFile -Raw)).Trim()
  }
  $idValue=[guid]::Empty
  if(-not [guid]::TryParse($workerId,[ref]$idValue)){
    $workerId=[guid]::NewGuid().ToString('D')
    [IO.File]::WriteAllText($WorkerIdFile,$workerId,(New-Object Text.UTF8Encoding($false)))
  }
  $running=@()
  if(Get-Command docker -ErrorAction SilentlyContinue){
    try {
      $running=@(& docker compose --profile '*' ps --status running --services 2>$null)
      if($LASTEXITCODE -ne 0){$running=@()}
    }catch{ $running=@() }
  }
  $running=@($running | ForEach-Object {$_.Trim()} | Where-Object {$_})
  $hasWhisper=$running -contains 'whisper'
  $hasQwen=$running -contains 'qwen-stream'
  $hasOllama=($running -contains 'ollama') -and ($running -contains 'ollama-gateway')
  $selectedModel=''
  if($hasOllama){
    try {
      $models=@((Invoke-RestMethod -Uri ('http://'+$ip+':11434/api/tags') -TimeoutSec 2).models |
        ForEach-Object {if($_.name){[string]$_.name}})
      if($models -contains 'qwen3:4b-instruct'){$selectedModel='qwen3:4b-instruct'}
      elseif($models.Count -eq 1){$selectedModel=[string]$models[0]}
    }catch{ $selectedModel='' }
  }
  $manifest=[ordered]@{
    schema='tafa-connection-v1'
    kind='gpu_worker'
    device_id=$workerId
    host=$ip
    services=[ordered]@{
      wyoming_stt=[ordered]@{host=$ip;port=10300;enabled=$hasWhisper}
      qwen_tts=[ordered]@{url=('http://'+$ip+':10502');enabled=$hasQwen}
      ollama=[ordered]@{url=('http://'+$ip+':11434');enabled=$hasOllama;model=$selectedModel}
    }
  }
  $json=$manifest | ConvertTo-Json -Depth 7
  [IO.File]::WriteAllText($Report,[string]$json,(New-Object Text.UTF8Encoding($false)))
  # The TXT and JSON are generated from one manifest snapshot.
  $whisperState=if($manifest['services']['wyoming_stt']['enabled']){'aktiv'}else{'nicht gestartet'}
  $qwenState=if($manifest['services']['qwen_tts']['enabled']){'aktiv'}else{'nicht gestartet'}
  $ollamaState=if($manifest['services']['ollama']['enabled']){'aktiv'}else{'nicht gestartet'}
  $modelText=if($selectedModel){$selectedModel}else{'kein Modell erkannt'}
  $lines=@(
    'TAFA GPU Worker - Verbindungsdaten'
    '=================================='
    ('GPU-LAN-IP: '+$manifest['host'])
    ('Worker-ID: '+$manifest['device_id'])
    ''
    '1. GPU Whisper / Wyoming (STT)'
    ('   Host: '+$manifest['services']['wyoming_stt']['host'])
    ('   Port: '+$manifest['services']['wyoming_stt']['port'])
    ('   Status: '+$whisperState)
    '   Home Assistant: Geraete & Dienste > Wyoming Protocol hinzufuegen.'
    '   TAFA > Verbindungen: GPU-Schnellerkennung = GPU-LAN-IP.'
    '   TAFA > Verbindungen > GPU/KI: GPU-Wyoming-STT-Entitaet waehlen.'
    ''
    '2. Qwen (Sprachausgabe / TTS)'
    ('   Adresse: '+$manifest['services']['qwen_tts']['url'])
    ('   Status: '+$qwenState)
    '   TAFA > Verbindungen: Qwen-TTS-Adresse.'
    ''
    '3. Ollama (Text-KI, optional)'
    ('   Adresse: '+$manifest['services']['ollama']['url'])
    ('   Status: '+$ollamaState)
    ('   Modell: '+$modelText)
    '   Home Assistant: Geraete & Dienste > Ollama hinzufuegen.'
    '   TAFA > Verbindungen > GPU/KI: Ollama conversation.*-Entitaet waehlen.'
    ''
    '4. Automatische Einrichtung'
    '   TAFA > Verbindungen > Schnelleinrichtung per JSON.'
    '   Datei: tafa-worker.json (nur GPU-Dienste; CPU getrennt einrichten)'
    ''
    '5. CPU-Fallback separat einrichten (nicht Teil des GPU-Exports)'
    '   TAFA lokal: CPU-Whisper und Piper werden von der TAFA-App bereitgestellt.'
    '   Extern: CPU-Whisper via Wyoming Protocol, TCP 10300.'
    '   Extern: Piper HTTP-Adresse des CPU-Servers, typischerweise Port 5000.'
    '   TAFA > Verbindungen > CPU-Fallback: Piper und CPU-Wyoming pruefen.'
    '   CPU- und GPU-STT-Entitaeten duerfen nicht identisch sein.'
    '   Ein CPU-LLM-Fallback fuer Ollama wird hierdurch NICHT eingerichtet.'
    '   Die CPU-IP wird hier nicht geraten oder aus GPU-Adressen abgeleitet.'
    ''
    'Nicht gestartete GPU-Dienste sind im JSON als disabled gekennzeichnet.'
    'Keine Passwoerter oder API-Tokens enthalten.'
  )
  [IO.File]::WriteAllText($TextReport,($lines -join [Environment]::NewLine)+[Environment]::NewLine,(New-Object Text.UTF8Encoding($false)))
  Write-Host ('TAFA Import-JSON: '+$Report) -ForegroundColor Cyan
  Write-Host ('Adressuebersicht: '+$TextReport) -ForegroundColor Cyan
  Write-Host 'In TAFA > Verbindungen > Schnelleinrichtung per JSON importieren.'
}
try {
  Ensure-Env
  switch($Action) {
    'Prepare' { Write-Host 'Konfiguration erstellt; optional 01-Installieren.bat starten.' }
    'Install' {
      Check-Docker
      Compose -Arguments @('--profile','stream','config','--quiet')
      Compose -Arguments @('--profile','stream','up','-d','--build','whisper','qwen-stream')
      if(Ask-YesNo 'Optional Ollama als Text-KI mit einrichten?') { Setup-Ollama }
    }
    'Start' {
      Check-Docker
      Compose -Arguments @('--profile','stream','up','-d','whisper','qwen-stream')
      $known=@(& docker compose --profile llm ps --all --services 2>$null)
      if($LASTEXITCODE -eq 0 -and ($known -contains 'ollama')) {
        Compose -Arguments @('--profile','llm','up','-d','ollama','ollama-gateway')
      }
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
    'Ollama' { Setup-Ollama }
  }
  Write-Report
  if($Action -in @('Prepare','Install','Start')){
    Write-Host '04-Verbindungsdaten.bat oeffnet die TXT; JSON liegt daneben.' -ForegroundColor Cyan
  }
  Write-Host 'Fertig.' -ForegroundColor Green
  exit 0
}catch{
  Write-Host ('FEHLER: '+$_.Exception.Message) -ForegroundColor Red
  exit 1
}
