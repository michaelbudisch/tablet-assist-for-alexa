# TAFA GPU Worker 2.2.8 – Installation

[English](README.md) · [Schnellstart](../README.md) · [TAFA-Ersteinrichtung](../../docs/setup-guide.md)

Der GPU Worker ist **optional**. Er ergänzt die TAFA-CPU-Basis um GPU-Wyoming-Whisper (STT), Qwen-Streaming-Stimme (TTS) und ein gemeinsames Qwen3-VL-Modell über Ollama für Text/KI und Vision. Voraussetzung ist eine kompatible **NVIDIA-GPU**. Unter Windows: NVIDIA-Treiber, Docker Desktop mit **WSL2/Linux-Containern**. Unter Linux: Docker Engine mit Compose und NVIDIA Container Toolkit. Für die erstmaligen Modell-Downloads wird Internetzugang und genügend SSD-Speicher benötigt.

## Schnellstart Windows

Im Verzeichnis `worker/`:

1. `01-Installieren.bat` starten (optional vorher `00-Konfiguration.bat`). Es startet GPU-Whisper und Qwen-TTS und installiert automatisch **`qwen3-vl:4b-instruct` als einziges Ollama-Modell** für Text und Vision (mehrere GB). Anschließend lädt es das Modell in den Speicher und behält es, sofern GPU-/Systemspeicher reichen.
2. `02-Starten.bat` startet konfigurierte Dienste; `03-Neustarten.bat` startet laufende Container neu.
3. `04-Verbindungsdaten.bat` erzeugt **`tafa-worker.json`** und **`GPU-Worker-Verbindungsdaten.txt`**, öffnet die TXT und startet **keine** Dienste. Exportwerte stammen aus der `LAN_IP` der lokalen `.env` und dem aktuell erkannten Containerstatus. Nicht gestartete Dienste stehen als `enabled: false` im JSON.
4. Im **TAFA Control Center → Verbindungen → Schnelleinrichtung per JSON** die Datei `tafa-worker.json` auswählen, **Konfiguration prüfen** und die GPU-Werte übernehmen. Danach die echten HA-Entitäten wie unten beschrieben zuordnen.

Eine bestehende Installation kann Vision mit **`05-Vision-Einrichten.bat`** nachrüsten, ohne Whisper oder Qwen neu zu installieren. Weitere Windows-Werkzeuge liegen in `scripts/windows/`, etwa `05-Ollama-Einrichten.bat`, `Worker-Windows.ps1` und `tests/`. Bestehende `.env`-Dateien und Docker-Volumes werden nicht überschrieben.

## Linux und manueller Docker-Start

Vom Verzeichnis `worker/` aus:

```bash
bash scripts/linux/setup-linux.sh
docker compose config --quiet
docker compose up -d --build whisper
docker compose --profile stream up -d --build qwen-stream
```

Gemeinsames **Text-/Vision-Modell** über Ollama:

```bash
docker compose --profile vision up -d --build ollama ollama-gateway vision
docker compose --profile vision exec ollama ollama pull qwen3-vl:4b-instruct
```

Nach dem ersten Linux-Start einmal vorladen (GPU-IP ersetzen):

```bash
curl -sS -X POST http://GPU-IP:11434/api/generate -H 'Content-Type: application/json' -d '{"model":"qwen3-vl:4b-instruct","prompt":"","stream":false,"keep_alive":-1}'
```

Die automatisierte Windows-Erzeugung der JSON-/TXT-Dateien ist für Linux **nicht** enthalten. Die Adressen unter TAFA **Verbindungen** deshalb dort manuell eintragen. Alle Dienste teilen die GPU. Ein dauerhaft geladenes Qwen3-VL benötigt zusammen mit Whisper und Qwen-TTS genügend VRAM; bei Speichermangel kann Ollama auf langsameren RAM/CPU-Offload ausweichen.

## Welche Adresse wohin?

| Dienst | GPU-Adresse | Einmalige HA-Einrichtung | TAFA Control Center |
| --- | --- | --- | --- |
| GPU Whisper/STT | `GPU-IP:10300` | **Wyoming Protocol** als neue Integration hinzufügen und deren `stt.*`-Entität ermitteln | **Verbindungen → GPU/KI:** GPU-Wyoming-STT und **GPU-PC-IP für Schnellprüfung** (nur IP) |
| Qwen/TTS | `http://GPU-IP:10502` | In Assist die TAFA-TTS-Entität **Tablet Assist Stream** nutzen | **Verbindungen → GPU/KI:** Qwen-TTS-Adresse |
| Ollama/Text und Vision | `http://GPU-IP:11434` | **Ollama**-Integration hinzufügen, Textmodell und Konversationsagent einrichten | **Verbindungen → GPU/KI:** echte `conversation.*`-Entität |
| CPU-Reserve | Extern: `CPU-IP:10300` und `http://CPU-IP:5000`; lokal: TAFA-App | Extern **zusätzliches Wyoming Protocol** für CPU-STT, andere `stt.*`-Entität als GPU | **Verbindungen → CPU-Fallback**; Sprachmodus unter **Einstellungen** |

**Wichtig:** GPU-Qwen/TTS aktiviert **nicht** GPU-Wyoming/STT. Erst die HA-Wyoming-Integration stellt die GPU-`stt.*`-Entität bereit. Der JSON-Export kennt **nur den GPU-Rechner**; CPU/Proxmox-Adresse, Raumzuordnungen und HA-Entitäten werden weder geraten noch im JSON miterzeugt. Die `tafa-worker.json` muss deshalb mit **Wyoming und Ollama in HA** vervollständigt werden.

**Fallback:** **Tablet Assist Sprachrouter** kann von GPU-Whisper auf eine eingerichtete CPU-STT zurückfallen; **Tablet Assist Stream** von GPU-Qwen auf Piper, sofern Qwen vor Wiedergabebeginn ausfällt. Ein ausgefallenes GPU-Ollama wird dadurch **nicht** automatisch durch ein CPU-LLM ersetzt. Falls die freie KI auch ohne GPU funktionieren soll, ist ein gesonderter CPU-Konversationsagent nötig.

## Testen und Betrieb

In TAFA **Verbindungen** die Dienste prüfen; danach in der Pipeline **TAFA Lokal** die drei Router kontrollieren. Eine echte Frage zuerst mit GPU und danach mit gestoppter GPU stellen. Die Attribute der STT-Router-Entität zeigen an, ob CPU oder GPU verwendet wurde. Ein TCP-Check allein belegt keine erfolgreiche Transkription. Browser-Tests unter **Jetzt sprechen** verwenden Browser-Audio; eine Echo-Ausgabe muss zusätzlich am Android-Tablet geprüft werden.

Qwen stellt `/health`, `/stream` und `/synthesize` auf Port **10502** bereit. Das ältere nicht-streamende TTS-Profil nutzt **10501** und soll nicht gleichzeitig mit dem Streamingmodell laufen. Vision wird im Windows-Installer nun aktiv angeboten; Nachrüstung mit **`05-Vision-Einrichten.bat`**. Unter Linux/manuell: `docker compose --profile vision up -d --build ollama vision` und erst nach Zustimmung `docker compose --profile vision exec -T ollama ollama pull qwen3-vl:4b-instruct`. Test: `http://GPU-IP:10503/health` muss `ready: true` melden. Der Vision-Container kann auch laufen, wenn das Modell fehlt – dann ist er **nicht bereit**. Der Adressbericht nennt Container- und Modellstatus; im JSON-v1 bleiben aus Kompatibilitätsgründen nur die bisherigen Dienste. HA leitet den Vision-Port aus der gespeicherten GPU-TTS-Adresse ab. Die Kamera-Freigabe in HA ist ein separater Schritt. Fortgeschrittene/ältere technische Details stehen im [historischen Worker-Referenztext](archive/legacy-worker-guide.de.md).

**Sicherheit:** Tokenfreie Worker-APIs sind **keine öffentlichen Internetdienste**. Ports **10300**, **10502**, **10503**, **11434** und ggf. **10501** nur für vertrauenswürdige Geräte/HA per LAN/Firewall freigeben. Keine Portweiterleitungen oder öffentlichen Worker-Proxies einrichten. Die `.env`, JSON- und TXT-Dateien mit lokalen IPs nicht in Git hochladen.
