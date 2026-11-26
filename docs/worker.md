# Optionaler TAFA GPU Worker

[English](en/worker.md) · [TAFA installieren](setup-guide.md)

Der **GPU Worker 2.2.5** erweitert TAFA um GPU-Wyoming-Whisper (Port **10300**), Qwen-Streaming-TTS (Port **10502**), optional Ollama (Port **11434**) und Vision (Port **10503**). Die **CPU-Sprachdienste** sind unabhängig davon: **TAFA lokal** oder ein **externer Sprachserver**. Nur im privaten, per Firewall beschränkten LAN betreiben.

**Windows:** Im Ordner `worker/` **01-Installieren.bat** starten, danach **04-Verbindungsdaten.bat** für `tafa-worker.json` und `GPU-Worker-Verbindungsdaten.txt`. Unter **TAFA → Verbindungen → Schnelleinrichtung per JSON** importieren, **prüfen und übernehmen**. Die CPU-Verbindungen werden separat eingerichtet.

**Home Assistant:** Für GPU-Whisper unter **Geräte & Dienste** die Integration **Wyoming Protocol**, GPU-IP und Port **10300** hinzufügen, dann die **GPU-`stt.*`-Entität in TAFA → Verbindungen** auswählen. GPU-PC-IP für Schnellprüfung **ohne Port** angeben. Für Ollama bei Bedarf zusätzlich eine HA-**Ollama**-Integration und `conversation.*`-Entität anlegen. **Qwen-TTS aktiviert Wyoming nicht automatisch.**

**Sprachpipeline:** STT **Tablet Assist Sprachrouter**, Gespräch **Tablet Assist Gesprächsrouter**, TTS **Tablet Assist Stream**. GPU-Whisper kann zu CPU-Whisper, GPU-Qwen zu Piper zurückfallen, **aber Ollama/Text-KI hat ohne weitere Einrichtung keinen CPU-LLM-Fallback**.

Alle Befehle, Linux-Schritte, Tests, Voraussetzungen und optionales Vision stehen in der [vollständigen Worker-Installationsanleitung](../worker/docs/README.de.md). Die [Worker-README](../worker/README.md) enthält den Windows-Schnellstart.
