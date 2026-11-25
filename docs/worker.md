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

## 3. Home Assistant und CPU-Sprachserver verbinden

GPU-Wyoming in HA über die Host-IP und Port 10300 hinzufügen; Entity-ID in der HA-Konfigurationsvorlage als `gpu_stt` eintragen. GPU-Host ohne zusätzlichen Token im Integrationsdialog ergänzen; bei Altinstallation die Vorlagen verwenden. Für MP3-Durchsagen in `/etc/jarvis-local.env` die eigenen Werte einstellen:

```ini
JARVIS_GPU_BASE=http://gpu.example.invalid:10502
```

Datei nur lokal, root-only. `systemctl restart jarvis-mp3`. Im Dashboard Automatisch wählen. Ohne GPU oder bei einem Fehler vor Audiobeginn bleibt Piper als Reserve. Der alte `worker/proxmox/tts_router.py` ist nur eine Referenz des Originalarchivs, nicht zusätzlich zum Hauptinstaller installieren.

## 4. Testen

Windows: `Test-Stream.ps1`, `Test-Voice.ps1` aus dem Worker-Verzeichnis. Linux: mit eigenen lokalen Werten ohne API-Token `/health`, `/synthesize` und `/stream` prüfen. Keine Konfigurationsdateien mit privaten Netzwerkdaten veröffentlichen. Anschließend native Assist-Ausgabe und MP3 bei ausgeschaltetem GPU-Rechner prüfen.

## Jarvis-Modelleinstellungen (1.8.0)

Mit der TAFA-HA-Integration 0.4.3 lassen sich unter **KI & Leistung** installierte Text- und Bildmodelle, Kontext (2048/4096/8192 Tokens) und Warmhaltezeit (0/60/120/300/600 Sekunden) zentral wählen. Für gemeinsamen Betrieb beide Modelle auf `qwen3-vl:4b-instruct` setzen; getrennt Qwen3 4B Instruct als Textmodell und Qwen3-VL 4B Instruct als Bildmodell wählen. Ollama lädt höchstens ein Modell und verarbeitet eine Anfrage gleichzeitig. GPU-Speicherbedarf gemeinsam mit STT und TTS prüfen. Keine automatischen Downloads oder zusätzlichen Dienste. Ältere Vision-Aufrufe entladen standardmäßig sofort.

Der auf das vertrauenswürdige LAN zu beschränkende Aufruf `GET /runtime` meldet ausschließlich unterstützte installierte und geladene Modelle. `POST /describe` erlaubt begrenzte Werte für `keep_alive` und `num_ctx` und liefert Zeitmessungen. HA übergibt gespeicherte Einstellungen und aktualisiert den bestehenden Ollama-Gesprächsagenten, ohne Prompts, Werkzeuge oder Verlauf zu verändern. Browser erhalten keinen Worker-Schlüssel. Reine Kameraanzeigen umgehen beide Modelle. Änderungen gelten ab der nächsten Anfrage; die erste Anfrage nach Leerlauf kann länger dauern. Bestehende `.env` und Volumes erhalten; beim Update nur Vision neu bauen. Kein APK-Update erforderlich.
