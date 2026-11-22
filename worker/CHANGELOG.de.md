[English](CHANGELOG.md) | **Deutsch**

# 1.6.0

- Optionaler authentifizierter Einzelbilddienst über vorhandenes Ollama; vier erlaubte Modelle, Qwen3-VL 4B Instruct Standard.
- Feste Beschreibungsmodi, Bildlimits, Metadatenentfernung, eine parallele Vision-Anfrage, Entladen nach Inferenz. Keine Aufnahme oder Bildablage.
- Simulierte API-Tests und PowerShell-Testclient. Sprach-/Textdienste unverändert. GPU und HA-Kameraanbindung am Zielsystem testen.

# 1.5.0
- Authentifizierte Stimmvariantenauswahl 1–9 für vorhandene synthetische Referenzen; fehlende Varianten fallen auf die konfigurierte Referenz zurück. Status im Antwortheader. Keine Uploads oder entfernten Modellneuladungen.
- Lokales prepare_variants.py erstellt weitere Varianten bei gestopptem Streaming-Container. Bestehende Referenzen bleiben erhalten.
- LLM, STT, Schlüssel, Ports und Standardstimme unverändert. Statische/Stubbing-Tests; GPU und Klang am Zielgerät prüfen.

# 1.4.0
- Fixed-Modus: einmalige synthetische VoiceDesign-Referenz im persistenten Modellvolume, wiederverwendet beim Streaming mit Qwen Base.
- Separater Design-Prozess beendet sich vor dem Laden des Base-Modells. Design, styled und fast bleiben verfügbar.
- Optionale 0.6B-Variante, neue Stilbeschreibung oder Varianten-ID erzeugt eine weitere gespeicherte Referenz.
- API, Token, LAN-Port, Audioformat, Whisper und Ollama unverändert; echte CUDA-/Stimmtests ausstehend.

# 1.3.0
- Optionaler lokaler Ollama-GPU-Dienst, ein Modell, eine parallele Anfrage, Kontext 4096 und Entladen bei Leerlauf.
- Authentifizierter LAN-Proxy, bestehender Worker-Schlüssel. Kein direkter Ollama-Port oder Modellverwaltungsendpunkte.
- Qwen3 4B Instruct und HA-Ollama-Einrichtung dokumentiert.
- STT/TTS-Dienste, Image-Tags und Volumes unverändert. Modellinstallation und GPU-Laufzeit prüfen.

# 1.2.0
- Streaming-Stimmprofile fast (0.6B), styled und design (1.7B).
- Konfigurierbare Stimmbeschreibung, unveränderte authentifizierte API und PCM.
- Test-Voice.ps1 erzeugt und spielt lokal WAV. Fast bleibt Standard; GPU-Speicher/Modelllaufzeit prüfen.

# 1.1.1
- Transformers 5.15.1 und qwen-tts-hf 0.1.1.post1 für Encoder-Kompatibilität festgeschrieben und beim Build überprüft.
- Whisper, Qwen, Modellcache und .env unverändert.

# 1.1.0
- Optionales Faster-Qwen-Streaming auf LAN-Port 10502; authentifiziertes PCM und WAV. Whisper und ursprünglicher Qwen-Dienst unverändert.

# 1.0.1
- Compose-GPU-Reservierungen statt gpus-Schlüssel. Konfiguration und Volumes bleiben erhalten.

# 1.0.0
- Optionales GPU-Whisper über Wyoming, separater Qwen3-TTS-Dienst.
- Private LAN-Bindung, Token-Schutz und lokaler WAV-Test.
- Separater Proxmox-TTS-Fallback-Proxy, nicht automatisch aktiviert.
