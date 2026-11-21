# Optionaler KI-Zusatzrechner – Original-Worker v1.5.0

Enthalten ist der bereitgestellte Jarvis GPU Worker 1.5.0. Modelle sind nicht enthalten; beim ersten Build/Start werden sie separat geladen. Windows: Docker Desktop mit WSL2 und NVIDIA-Treiber. Linux: Docker Engine mit Compose und NVIDIA Container Toolkit. Genügend SSD-Speicher für Modelle einplanen. Zugriff nur im vertrauenswürdigen privaten Netz; Ports nicht ins Internet freigeben. GPU-Inferenz und Linux-Setup sind in dieser Vorschau nicht Ende-zu-Ende getestet.

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

## 3. Home Assistant und CPU-Sprachserver verbinden

GPU-Wyoming in HA über die Host-IP und Port 10300 hinzufügen; Entity-ID in der HA-Konfigurationsvorlage als `gpu_stt` eintragen. GPU-Host und API-Token in HA ergänzen. Für MP3-Durchsagen in `/etc/jarvis-local.env` die eigenen Werte einstellen:

```ini
JARVIS_GPU_BASE=http://gpu.example.invalid:10502
JARVIS_TTS_TOKEN=REPLACE_WITH_WORKER_TOKEN
```

Datei nur lokal, root-only. `systemctl restart jarvis-mp3`. Im Dashboard Automatisch wählen. Ohne GPU oder bei einem Fehler vor Audiobeginn bleibt Piper als Reserve. Der alte `worker/proxmox/tts_router.py` ist nur eine Referenz des Originalarchivs, nicht zusätzlich zum Hauptinstaller installieren.

## 4. Testen

Windows: `Test-Stream.ps1`, `Test-Voice.ps1` aus dem Worker-Verzeichnis. Linux: mit eigenen lokalen Werten und API-Token `/health`, `/synthesize` und `/stream` prüfen. Keine Token in Screenshots, Logs oder Commit-Verlauf. Anschließend native Assist-Ausgabe und MP3 bei ausgeschaltetem GPU-Rechner prüfen.
