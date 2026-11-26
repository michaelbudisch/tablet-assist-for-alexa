# TAFA GPU Worker 2.2.5

**[Deutsch: Installationsanleitung](docs/README.de.md)** · **[English installation guide](docs/README.md)** · [Projekt](../README.de.md)

### Windows – Schnellstart

1. **01-Installieren.bat** – erstellt bei Bedarf die lokale `.env`, startet Whisper/Qwen und fragt nach optionaler Ollama-Einrichtung und einem Modelldownload.
2. **02-Starten.bat** – startet die eingerichteten Dienste.
3. **03-Neustarten.bat** – startet laufende Container neu.
4. **04-Verbindungsdaten.bat** – erstellt die TAFA-Importdatei `tafa-worker.json` und die lesbare `GPU-Worker-Verbindungsdaten.txt`; die TXT wird geöffnet.

Optional: `00-Konfiguration.bat` erstellt nur eine fehlende `.env`. Der manuelle Ollama-Nachinstaller liegt unter `scripts/windows/05-Ollama-Einrichten.bat`. Linux: `scripts/linux/setup-linux.sh`.

**TAFA-Einrichtung:** Control Center → **Verbindungen** → **Schnelleinrichtung per JSON**. Eintragungen werden vor der Übernahme geprüft.

**CPU-Fallback:** Whisper (STT) läuft auf dem Proxmox-Sprachserver über Wyoming, Piper (TTS) auf dem Homeserver. GPU-JSON und TXT enthalten ausschließlich die GPU-Adressen.

**Sicherheit:** Keine API-Tokens in den Exportdateien; Worker-Endpunkte nur im vertrauenswürdigen LAN verwenden, keine Router-Portfreigaben. Vorhandene `.env` und Modellvolumes werden nicht überschrieben.

[Changelog (DE)](docs/CHANGELOG.de.md) · [Changelog (EN)](docs/CHANGELOG.md)
