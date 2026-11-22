**Deutsch** | [English](en/worker.md) · [Projektübersicht](../README.de.md)

# Optionaler KI-Zusatzrechner – Original-Worker v1.8.0

Enthalten ist der bereitgestellte Jarvis GPU Worker 1.7.0. Modelle sind nicht enthalten; beim ersten Build/Start werden sie separat geladen. Windows: Docker Desktop mit WSL2 und NVIDIA-Treiber. Linux: Docker Engine mit Compose und NVIDIA Container Toolkit. Genügend SSD-Speicher für Modelle einplanen. Zugriff nur im vertrauenswürdigen privaten Netz; Ports nicht ins Internet freigeben. GPU-Inferenz und Linux-Setup sind in dieser Vorschau nicht Ende-zu-Ende getestet.

## 1. Konfiguration

Windows PowerShell aus dem Ordner `worker/`:

```powershell
.\Setup.ps1
```

Linux aus `worker/`:

```bash
bash setup-linux.sh
```

Beide Skripte erzeugen eine lokale `.env` mit zufälligem API-Token; bestehende Dateien werden nicht überschrieben. Den Schlüssel niemals veröffentlichen. Firewall: den Wyoming-Port 10300 auf HA, TTS-Port 10502 auf HA und den CPU-Sprachserver begrenzen; bei Ollama Port 11434 auf HA beschränken.

## 2. Dienste starten

Im Ordner `worker/`:

```bash
docker compose config --quiet
docker compose up -d --build whisper
docker compose --profile stream up -d --build qwen-stream
```

Streaming unterstützt `/health`, `/stream` (24 kHz PCM s16le-mono) und `/synthesize`. Port 10501 mit dem Profil `tts` ist die ältere nicht streamende Variante; nicht gleichzeitig mit dem Streaming-Modell starten. Stimmvarianten werden lokal vorbereitet; siehe [Original-Worker-Dokumentation](../worker/README.md).

Optional lokales LLM:

```bash
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
```

Ollama verwendet dieselbe GPU. Bei knappem VRAM die Dienste einzeln testen. Die geschützte Ollama-Schnittstelle kann über die HA-Ollama-Integration eingebunden werden; Schlüssel nur im HA-Dialog eingeben. Modelle können sich gegenseitig Speicher entziehen. Kein GPU-Rechner nötig für die CPU-Basis.

## Optional: Vision

Visionprofil über vorhandenes Ollama, Port 10503 nur für HA. [Installation und API](../worker/README.md). Kameraauswahl in HA folgt separat.

## 3. Home Assistant und CPU-Sprachserver verbinden

GPU-Wyoming in HA über die Host-IP und Port 10300 hinzufügen; Entity-ID in der HA-Konfigurationsvorlage als `gpu_stt` eintragen. GPU-Host und API-Token im Integrationsdialog ergänzen; bei Altinstallation die Vorlagen verwenden. Für MP3-Durchsagen in `/etc/jarvis-local.env` die eigenen Werte einstellen:

```ini
JARVIS_GPU_BASE=http://gpu.example.invalid:10502
JARVIS_TTS_TOKEN=REPLACE_WITH_WORKER_TOKEN
```

Datei nur lokal, root-only. `systemctl restart jarvis-mp3`. Im Dashboard Automatisch wählen. Ohne GPU oder bei einem Fehler vor Audiobeginn bleibt Piper als Reserve. Der alte `worker/proxmox/tts_router.py` ist nur eine Referenz des Originalarchivs, nicht zusätzlich zum Hauptinstaller installieren.

## 4. Testen

Windows: `Test-Stream.ps1`, `Test-Voice.ps1` aus dem Worker-Verzeichnis. Linux: mit eigenen lokalen Werten und API-Token `/health`, `/synthesize` und `/stream` prüfen. Keine Token in Screenshots, Logs oder Commit-Verlauf. Anschließend native Assist-Ausgabe und MP3 bei ausgeschaltetem GPU-Rechner prüfen.

## Jarvis model settings / Modelleinstellungen (1.8.0)

With Jarvis Tablet Audio 1.5.0, the dashboard's **AI models and performance** panel selects installed text and vision models and a matching context (2048/4096/8192 tokens) and residency (0/60/120/300/600 seconds). Selecting `qwen3-vl:4b-instruct` for both avoids alternating model weights; verify real VRAM peaks alongside Whisper and TTS. Ollama still permits one loaded model and one parallel request. No automatic downloads, new service, public Ollama endpoint or volume changes are added. Legacy vision callers retain immediate unload by default.

The authenticated `GET /runtime` reports only allowlisted installed/loaded models. `POST /describe` additionally accepts bounded `keep_alive` and `num_ctx` and reports inference timing metrics. The HA integration supplies saved parameters; its existing Ollama conversation agent receives matching settings through native config-subentry persistence, preserving prompts, tools and history. Browser clients never receive the worker key. Camera-display commands still bypass both inference models. Settings changes apply on the next request; the first request after idle/restart may load the model.

DE: Unter **Jarvis → Assistent und Audio → KI-Modelle und Leistung** Text-/Bildmodell, Warmhaltezeit und Kontext wählen. Für gemeinsamen Betrieb beide Modelle auf Qwen3-VL 4B Instruct setzen und speichern. Zurückwechseln: Textmodell Qwen3 4B Instruct, Bildmodell Qwen3-VL 4B Instruct. Die Einstellungen gelten zentral für alle Jarvis-Geräte. Höhere Kontextwerte benötigen mehr GPU-Speicher. Vorhandene `.env`, Modelle und Volumes behalten; beim Update nur den Dienst `vision` neu bauen/starten. Kein APK-Update erforderlich.
