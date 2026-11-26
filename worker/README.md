# TAFA GPU Worker 2.2.5

[Deutsch: Installationsanleitung](docs/README.de.md) · [English installation guide](docs/README.md) · [TAFA Projekt](../README.de.md)

Der GPU Worker ist eine **optionale** Ergänzung für GPU-Whisper, Qwen-TTS, Ollama und Vision. Die CPU-Basis kommt **wahlweise** aus der TAFA-App (**lokal**) oder einem separaten CPU-Sprachserver (**extern**).

## Windows-Schnellstart

1. **01-Installieren.bat** – fehlende `.env` erzeugen, Whisper/Qwen starten; optional Ollama und Modell-Download nach Zustimmung.
2. **02-Starten.bat** – konfigurierte Dienste starten.
3. **03-Neustarten.bat** – laufende Container neu starten.
4. **04-Verbindungsdaten.bat** – `tafa-worker.json` und `GPU-Worker-Verbindungsdaten.txt` erstellen; die TXT wird geöffnet.

Optional: **00-Konfiguration.bat** nur für die fehlende `.env`, **scripts/windows/05-Ollama-Einrichten.bat** für Ollama später. Linux: **scripts/linux/setup-linux.sh**; dort werden HA-Verbindungsdaten derzeit manuell eingetragen.

**TAFA → Verbindungen → Schnelleinrichtung per JSON**: Import prüfen und bestätigen. Anschließend in Home Assistant die **Wyoming Protocol**-Integration für die GPU (Port **10300**) hinzufügen und die neu erzeugte GPU-`stt.*`-Entität in **Verbindungen** auswählen. Ollama benötigt separat die HA-Ollama-Integration und einen `conversation.*`-Agenten.

**CPU-Fallback:** Externes CPU-Whisper via separatem Wyoming (10300) und Piper HTTP (5000), oder beide CPU-Dienste direkt in der TAFA-App. Das GPU-JSON enthält **keine** erfundene CPU-Adresse und aktiviert keinen CPU-LLM-Fallback.

**Sicherheit:** Worker-Dienste nur im vertrauenswürdigen LAN, keine Internet-Portfreigaben; `.env`, JSON/TXT mit privaten IPs lokal halten. Bei Updates bleiben vorhandene `.env` und Modell-Volumes bestehen.

[Änderungen DE](docs/CHANGELOG.de.md) · [Changelog EN](docs/CHANGELOG.md)
