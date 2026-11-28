# TAFA GPU Worker 2.2.8

[Deutsch: Installationsanleitung](docs/README.de.md) · [English installation guide](docs/README.md) · [TAFA Projekt](../README.de.md)

Der GPU Worker ist eine **optionale** Ergänzung für GPU-Whisper, Qwen-TTS, Ollama und Vision. Die CPU-Basis kommt **wahlweise** aus der TAFA-App (**lokal**) oder einem separaten CPU-Sprachserver (**extern**).

## Stimmenvarianten in TAFA

Mit Worker 2.2.8 zeigt **TAFA → Einstellungen → Stimme und Klang** alle Varianten 1–9 mit ihrem echten Status. Fehlende Profile können dort einzeln erstellt und anschließend per Hörprobe getestet werden. Für die Erstellung ist `STREAM_VOICE_MODE=fixed` in der Worker-`.env` erforderlich. Die Standardstimme bleibt bestehen; weitere Stimmen nutzen bewusst unterschiedliche synthetische Stimmcharaktere. Eine neue Variante wird erst nach **Einstellungen speichern** für TAFA ausgewählt.

**Bereits eingerichteter Windows-GPU-Worker:** die aktuellen Worker-Dateien übernehmen und **06-Stimmenverwaltung-Aktualisieren.bat** ausführen. Nur Qwen-Stream wird neu gebaut; Ollama, Whisper, Vision und persistente Modelle werden nicht gelöscht. Das Vorbereiten einer Stimme belegt die GPU vorübergehend; dabei kann Piper übernehmen.

## Windows-Schnellstart

1. **01-Installieren.bat** – fehlende `.env` erzeugen, GPU-Whisper und Qwen-TTS starten und **`qwen3-vl:4b-instruct` als einziges Ollama-Modell für Text und Vision installieren und vorladen**. Mehrere GB Download gehören zur Installation.
2. **02-Starten.bat** – konfigurierte Dienste starten.
3. **03-Neustarten.bat** – laufende Container neu starten.
4. **04-Verbindungsdaten.bat** – `tafa-worker.json` und `GPU-Worker-Verbindungsdaten.txt` erstellen; die TXT wird geöffnet.

Optional: **00-Konfiguration.bat** nur für die fehlende `.env`, **05-Vision-Einrichten.bat** zum Nachrüsten auf bestehenden GPU-Rechnern, **scripts/windows/05-Ollama-Einrichten.bat** als Kompatibilitätsalias für das gemeinsame Text-/Vision-Modell. Linux: **scripts/linux/setup-linux.sh**; dort werden HA-Verbindungsdaten derzeit manuell eingetragen.

**TAFA → Verbindungen → Schnelleinrichtung per JSON**: Import prüfen und bestätigen. Anschließend in Home Assistant die **Wyoming Protocol**-Integration für die GPU (Port **10300**) hinzufügen und die neu erzeugte GPU-`stt.*`-Entität in **Verbindungen** auswählen. Ollama benötigt separat die HA-Ollama-Integration und einen `conversation.*`-Agenten.

**Vision-Diagnose:** `04-Verbindungsdaten.bat` zeigt neu die lokale Vision-Adresse `http://GPU-IP:10503` und unterscheidet gestarteten Container von **tatsächlich bereitstehendem Modell** (`/health` mit `ready: true`). Die JSON-v1-Struktur bleibt unverändert, damit ältere TAFA-Installationen sie lesen können. Die Kamera-Vision-Adresse wird in HA aus der GPU-TTS-Adresse abgeleitet. Der eigene Vision-Dienst muss zusätzlich auf dem GPU-PC laufen.

**CPU-Fallback:** Externes CPU-Whisper via separatem Wyoming (10300) und Piper HTTP (5000), oder beide CPU-Dienste direkt in der TAFA-App. Das GPU-JSON enthält **keine** erfundene CPU-Adresse und aktiviert keinen CPU-LLM-Fallback.

**Sicherheit:** Worker-Dienste nur im vertrauenswürdigen LAN, keine Internet-Portfreigaben; `.env`, JSON/TXT mit privaten IPs lokal halten. Bei Updates bleiben vorhandene `.env` und Modell-Volumes bestehen.

[Änderungen DE](docs/CHANGELOG.de.md) · [Changelog EN](docs/CHANGELOG.md)
