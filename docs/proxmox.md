# CPU-Sprachserver

Voraussetzungen: aktuelles Proxmox VE oder Debian 12/13 mit systemd; für die CPU-Basis zunächst 4 vCPU, 4 GiB RAM und 20 GiB Speicher als Startgröße (abhängig vom Modell). Unterstützte Architektur und Python-Version der Abhängigkeiten prüfen. Eine NVIDIA-GPU ist nicht notwendig. Download der Modelle benötigt Internet; Laufzeit kann anschließend lokal bleiben.

## Neue VM/CT

In Proxmox eine Debian-Vorlage in der Oberfläche herunterladen. Repository auspacken/klonen. Auf dem Proxmox-Host als Administrator:

```bash
bash proxmox/create-ct.sh <freie-CT-ID> <Debian-Template-Volume> <Storage> [Bridge]
```

Das Skript fragt die CT-ID zur Bestätigung ab, erstellt nur einen neuen unprivilegierten CT (DHCP, kein Portforwarding) und installiert darin die Komponenten. Die Platzhalter ersetzen. Vorher Storage und Bridge prüfen. Für eine bereits vorhandene **leere** Debian-VM/CT stattdessen darin ausführen:

```bash
sudo bash proxmox/install-speechserver.sh
```

Das Skript verweigert die Installation auf dem PVE-Host und bei vorhandener Jarvis-Installation oder belegten Ports. Es installiert Python-Umgebung, Piper, Whisper, FFmpeg, MP3-API, temporäre Audioauslieferung, Systemd-Dienste und einen Cleanup-Timer. Es lädt eine deutsche Thorsten-Stimme herunter. Abhängigkeiten/Modelle können sich ändern; eine frische Installation ist noch nicht vollständig getestet.

## Prüfen

```bash
systemctl status jarvis-piper jarvis-mp3 jarvis-whisper jarvis-audio
curl -fsS http://127.0.0.1:5001/health
journalctl -u jarvis-whisper -n 50 --no-pager
```

Die lokale Konfiguration liegt unter `/etc/jarvis-local.env` (nur root). Den darin generierten `PIPER_API_TOKEN` lokal in Home Assistant als `piper_api_token` in `secrets.yaml` hinterlegen. Nicht in Git oder Chat posten. CPU-Host-Adresse und Port 10300 beim Wyoming-Setup angeben.

| Port | Dienst | Zugriff |
|---|---|---|
| 5000 | Piper HTTP (WAV) | nur interne vertrauenswürdige Clients |
| 5001 | MP3-API | intern, API-Schlüssel |
| 10300 | Wyoming STT | intern, kein öffentliches Netzwerk |
| 8080 | temporäre Audio-Dateien | intern; optional streng begrenzter HTTPS-Proxy |

Firewall-Regeln administrativ so setzen, dass lediglich die benötigten HA- und Proxy-Hosts zugreifen dürfen. Keine automatische Router-Konfiguration. Die GPU-Adresse bleibt zunächst leer; siehe `worker.md`.
