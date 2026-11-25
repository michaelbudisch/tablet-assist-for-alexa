# Optionaler KI-Zusatzrechner – GPU Worker 2.2.2

[English](en/worker.md) | **Deutsch** · [Projektübersicht](../README.de.md)

> **Schema-Update zu Worker 1.9.0:** Der lokale `/detect`-Endpunkt liefert zusätzlich `genders` mit den groben, unsicheren Erscheinungskategorien `man`, `woman`, `unknown`. Keine tatsächliche Geschlechts- oder Identitätsfeststellung. Vorhandene `.env` und Modellvolumes beibehalten, nur Vision neu bauen; HA-Backend gemeinsam aktualisieren. [HA-Automationen](ha-automations.md).

Enthalten ist der Jarvis GPU Worker 2.2.2 mit tokenfreier LAN-Kommunikation und vereinfachter Windows-Einrichtung. Modelle sind nicht enthalten; beim ersten Build/Start werden sie separat geladen. Windows: Docker Desktop mit WSL2 und NVIDIA-Treiber. Linux: Docker Engine mit Compose und NVIDIA Container Toolkit. Genügend SSD-Speicher für Modelle einplanen. Zugriff nur im vertrauenswürdigen privaten Netz; Ports nicht ins Internet freigeben. GPU-Inferenz und Linux-Setup sind in dieser Vorschau nicht Ende-zu-Ende getestet.

## 1. Konfiguration

Unter Windows im Ordner `worker/` per Doppelklick **00-Konfiguration.bat** und danach **01-Installieren.bat** ausführen. **02-Starten.bat** startet die Standarddienste, **03-Neustarten.bat** die laufenden Container neu und **04-Verbindungsdaten.bat** erzeugt eine lokale TXT-Datei mit LAN-IP und Ports. Alternativ bleibt `Setup.ps1` als kompatibler PowerShell-Einstieg erhalten.

Linux aus `worker/`:

```bash
bash setup-linux.sh
```

Die Einrichtungswege erzeugen eine lokale `.env` nur mit LAN-IP und Modelloptionen, **ohne API-Token**. Bestehende Dateien werden nicht überschrieben. Firewall: den Wyoming-Port 10300 auf HA, TTS-Port 10502 auf HA und den CPU-Sprachserver begrenzen; bei Ollama Port 11434 auf HA beschränken.

## 2. Dienste starten

Im Ordner `worker/`:

```bash
docker compose config --quiet
docker compose up -d --build whisper
docker compose --profile stream up -d --build qwen-stream
```

Streaming unterstützt `/health`, `/stream` (24 kHz PCM s16le-mono) und `/synthesize`. Port 10501 mit dem Profil `tts` ist die ältere nicht streamende Variante; nicht gleichzeitig mit dem Streaming-Modell starten. Stimmvarianten werden lokal vorbereitet; siehe [Original-Worker-Dokumentation](../worker/README.de.md).

Optional lokales LLM:

```bash
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
```

Ollama verwendet dieselbe GPU. Bei knappem VRAM die Dienste einzeln testen. Das tokenfreie Ollama-LAN-Gateway kann über die HA-Ollama-Integration eingebunden werden. Keine zusätzlichen TAFA-API-Schlüssel eingeben; den Gateway-Port ausschließlich für HA freigeben. Modelle können sich gegenseitig Speicher entziehen. Kein GPU-Rechner nötig für die CPU-Basis.

## Optional: Vision

Visionprofil über vorhandenes Ollama, Port 10503 nur für HA. [Installation und API](../worker/README.de.md). Kameraauswahl in HA folgt separat.

## 3. GPU-Whisper, CPU-Fallback und Ollama in Home Assistant einrichten

**Windows:** `04-Verbindungsdaten.bat` erstellt jetzt eine vollstaendige **deutsche und englische** Einrichtungs-TXT und oeffnet sie direkt in Notepad. Sie verwendet automatisch die GPU-LAN-IP aus der vorhandenen `.env`. Die GPU- und Proxmox-Adressen muessen getrennt eingegeben werden; die Proxmox-IP wird nicht erraten.

1. **Wyoming Protocol fuer GPU-Whisper installieren:** HA → **Einstellungen → Geraete & Dienste → Integration hinzufuegen → Wyoming Protocol**. Host = `GPU-IP`, Port = `10300`. Danach die neue `stt.*`-Entitaets-ID aus HA kopieren. In **Apps → TAFA → Konfiguration** als `gpu_stt` hinterlegen; `gpu_stt_host` = reine GPU-IP (kein Protokoll, kein Port).
2. **Wyoming Protocol fuer CPU-Whisper installieren:** Auch den Proxmox-CPU-Sprachserver ueber **Wyoming Protocol** an seiner eigenen IP, Port `10300` verbinden. Dessen separate STT-Entitaets-ID als `cpu_stt` eintragen. **Beide STT-Entitaets-IDs muessen verschieden sein**. Eine einzelne Wyoming-STT-Entitaet kann auto-ausgewaehlt werden; sobald CPU+GPU vorhanden sind, beide IDs explizit waehlen.
3. **Qwen-TTS konfigurieren:** `gpu_base=http://GPU-IP:10502` und `hardware_profile=automatic` in **Apps → TAFA → Konfiguration**. **GPU-Whisper wird dadurch nicht automatisch aktiviert.**
4. **Ollama-Integration fuer freie KI-Fragen:** Optional zuerst `docker compose --profile llm up -d ollama ollama-gateway` auf dem GPU-Rechner starten. Danach HA → **Geraete & Dienste → Integration hinzufuegen → Ollama** mit URL `http://GPU-IP:11434`. Ein bereits installiertes Textmodell (z. B. `qwen3:4b-instruct`) als Konversationsagent einrichten. **Die echte** `conversation.*`-Entitaets-ID aus HA in TAFA als `llm_agent` eintragen; nicht den Geraetenamen verwenden. **Ollama (Text-KI) ist ein anderer Dienst als Qwen (Sprachausgabe).**
5. **Assist-Pipeline TAFA Lokal pruefen:** STT = **Tablet Assist Sprachrouter** (GPU mit CPU-Fallback), Gespraech = **Tablet Assist Gespraechsrouter** (Ollama), TTS = **Tablet Assist Stream** (Qwen mit Piper-Fallback). Nach dem Speichern TAFA App neu starten, bei einer HA-Integrationsaktualisierung einmal HA Core neu starten.
6. **Laufzeit diagnostizieren:** Nach einer Frage unter Entwicklerwerkzeuge → Zustaende die `stt.*`-Entitaet **Tablet Assist Sprachrouter** anschauen: `letztes_backend=zusatzrechner` bedeutet GPU-Whisper; `homeserver` CPU/Fallback; `letzte_dauer_ms` misst inklusive Audioempfang. Die Android-Sprechpause und die Ollama-Antwortzeit beeinflussen die wahrgenommene Dauer ebenfalls.

Bei externem CPU-Sprachserver `speech_mode=external` und `external_piper_base=http://PROXMOX-IP:5000` einstellen. Fuer die alte dedizierte MP3-Durchsagen-Installation kann weiterhin in der **lokalen** `/etc/jarvis-local.env` die eigene GPU-Adresse stehen, z. B.:

```ini
JARVIS_GPU_BASE=http://gpu.example.invalid:10502
```

Datei nur lokal (root-only) halten; gegebenenfalls `systemctl restart jarvis-mp3`. Nicht zusaetzlich `worker/proxmox/tts_router.py` neben dem Hauptinstaller installieren. **Keine oeffentlichen Ports und keine Tokens fuer die Worker-LAN-Schnittstellen.**

## 4. Testen

Windows: `Test-Stream.ps1`, `Test-Voice.ps1` aus dem Worker-Verzeichnis. Linux: mit eigenen lokalen Werten ohne API-Token `/health`, `/synthesize` und `/stream` prüfen. Keine Konfigurationsdateien mit privaten Netzwerkdaten veröffentlichen. Anschließend native Assist-Ausgabe und MP3 bei ausgeschaltetem GPU-Rechner prüfen.

## Jarvis-Modelleinstellungen (1.8.0)

Mit der TAFA-HA-Integration 0.4.3 lassen sich unter **KI & Leistung** installierte Text- und Bildmodelle, Kontext (2048/4096/8192 Tokens) und Warmhaltezeit (0/60/120/300/600 Sekunden) zentral wählen. Für gemeinsamen Betrieb beide Modelle auf `qwen3-vl:4b-instruct` setzen; getrennt Qwen3 4B Instruct als Textmodell und Qwen3-VL 4B Instruct als Bildmodell wählen. Ollama lädt höchstens ein Modell und verarbeitet eine Anfrage gleichzeitig. GPU-Speicherbedarf gemeinsam mit STT und TTS prüfen. Keine automatischen Downloads oder zusätzlichen Dienste. Ältere Vision-Aufrufe entladen standardmäßig sofort.

Der auf das vertrauenswürdige LAN zu beschränkende Aufruf `GET /runtime` meldet ausschließlich unterstützte installierte und geladene Modelle. `POST /describe` erlaubt begrenzte Werte für `keep_alive` und `num_ctx` und liefert Zeitmessungen. HA übergibt gespeicherte Einstellungen und aktualisiert den bestehenden Ollama-Gesprächsagenten, ohne Prompts, Werkzeuge oder Verlauf zu verändern. Browser erhalten keinen Worker-Schlüssel. Reine Kameraanzeigen umgehen beide Modelle. Änderungen gelten ab der nächsten Anfrage; die erste Anfrage nach Leerlauf kann länger dauern. Bestehende `.env` und Volumes erhalten; beim Update nur Vision neu bauen. Kein APK-Update erforderlich.
