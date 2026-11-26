# GPU-Worker – Änderungsverlauf

## 2.2.6

- Windows-Installer bietet Vision-Bildanalyse standardmäßig aktiv an; der mehrgigabytegroße Modell-Download erfordert eine gesonderte Bestätigung. Keine automatische Modellinstallation ohne Einwilligung.
- `05-Vision-Einrichten.bat` rüstet Vision und Ollama auf einem bestehenden GPU-Worker nach, ohne Whisper-/Qwen-Einstellungen oder die vorhandene `.env` zu verändern.
- `02-Starten.bat` startet einen bereits eingerichteten Vision-Dienst nach Reboot erneut; `04-Verbindungsdaten.bat` zeigt Port 10503 und den Unterschied zwischen „Container gestartet“ und „Modell bereit“.
- Das bisherige `tafa-worker.json`-Schema bleibt kompatibel: Vision steht in der TXT, TAFA leitet seine URL aus der bekannten GPU-IP ab.
- Worker-Version, Docker-Image-Tags und Testverträge auf 2.2.6 aktualisiert.


## 2.2.5

- Installation bietet Ollama optional direkt in `01-Installieren.bat` an; Modelldownload nur mit ausdrücklicher Bestätigung.
- `tafa-worker.json` und `GPU-Worker-Verbindungsdaten.txt` werden beim Refresh aus denselben Daten erstellt. Die TXT zeigt IP, Ports und Dienststatus.
- Setup-/Testskripte nach `scripts/`, ausführliche Readmes und Changelogs nach `docs/` verschoben; Launcher, ZIP-Builder und CI-Pfade angepasst.
- Keine Änderungen an Ports, JSON-Schema, gespeicherten Modellen oder bestehender Home-Assistant-Installation.

## 2.2.4

- `04-Verbindungsdaten.bat` erstellt jetzt `tafa-worker.json` mit stabiler Worker-ID und tatsächlich gestarteten Whisper-, Qwen- und Ollama-Endpunkten. Ein Reimport identifiziert denselben Worker auch bei neuer IP. Keine Tokens oder Modelländerungen.


## 2.2.3

- `04-Verbindungsdaten.bat` schreibt nun nur noch eine kurze DE/EN-Liste der GPU-Endpunkte (Wyoming 10300, Qwen 10502, optional Ollama 11434) und ihrer genauen Eintragungsorte in Home Assistant oder TAFA. Keine langen Installationshinweise oder erfundenen Proxmox-IPs.
- `.env` und Docker-Volumes bleiben unverändert; Versionskennungen in allen Worker-Images konsistent aktualisiert.

## 2.2.2

- GPU-Worker-Verbindungsdaten sind jetzt ein **vollständiger DE/EN-Ersteinrichtungsleitfaden** mit der erkannten GPU-LAN-IP und konkreten Home-Assistant-/TAFA-Eingabefeldern, nicht nur eine Portliste.
- **Wyoming Protocol** für GPU-Whisper auf Port 10300 und separat für CPU-Whisper auf Proxmox beschrieben; **Ollama** als eigenständige HA-Integration für KI-Gespräche erklärt. Qwen-TTS auf 10502 ist weder Whisper noch Ollama.
- Anleitung zur Übernahme der echten `stt.*`- und `conversation.*`-IDs sowie zu `cpu_stt`, `gpu_stt`, `gpu_stt_host`, `gpu_base`, `llm_agent` und zur Diagnose mit `letztes_backend`.
- `04-Verbindungsdaten.bat` öffnet die generierte TXT direkt in Notepad. Vorhandene `.env`, Modelle, Dienste und tokenfreie LAN-Konfiguration bleiben erhalten.

## 2.2.1

- Zusätzliche TAFA-API-Token-Abfragen bei Qwen, Vision, Diagnose und Ollama im privaten LAN entfernt. Home-Assistant-Benutzeranmeldung bleibt erhalten.
- BAT-Dateien für Konfiguration, Installation, Start, Neustart und tokenfreie IP-/Portübersicht ergänzt.
- Setup.ps1 und setup-linux.sh erstellen .env ohne Token; vorhandene .env und Modellvolumes bleiben erhalten.
- GPU- und MP3-Generator-Ports nur im vertrauenswürdigen LAN mit Firewall-Freigaben verwenden, niemals Portweiterleitung ins Internet.


 
## 2.2.0

- Produktiver strukturierter Bildfolgen-Endpunkt mit begrenztem 12-Bild-Standard und 4-Bild-Detailprofil, striktem Schema und vorsichtiger Lieferbewertung. Gemeinsamer 16384-Kontext, bisherige Endpunkte kompatibel. Mock-Vertragstests ergänzt; GPU-Qualität und Laufzeiten erfordern Praxistest.

## 2.1.1

- Kontextüberlauf bei gemeinsamen Qwen3-VL-Benchmark-Anfragen behoben: begrenzter interner Mindestkontext 8192 Tokens für vier Frames und 16384 für acht oder zwölf. Einzelbild- und Produktiv-Anfragen bleiben unverändert. Angeforderter und tatsächlich verwendeter Kontext stehen in den Messdaten. Offline-Tests prüfen alle drei Größen; GPU-Speicher und Laufzeit müssen praktisch geprüft werden.

## 2.1.0

- Optionaler privater Endpunkt `/benchmark/sequence`: vier Bilder einzeln gegen 4, 8 oder 12 Bilder gemeinsam mit Qwen3-VL analysieren; bestehende Einzelbild-Endpunkte und Ring-Automationen bleiben unverändert.
- Lokaler MP4-Testläufer mit FFmpeg, identischen Referenzbildern, Zeitmessung und optionalem JSON-Ergebnisbericht ohne gespeicherte Videos, Bilder oder Zugangsdaten.
- Authentifizierung, strikte Grenzen für Frames, Zeitstempel, Modelle und Kontext sowie gemeinsame Vision-Warteschlange; keine Internet-Video-URLs oder direkten MP4-Uploads.
- Offline-Tests, Docker-Build und Dokumentation ergänzt; echte GPU-Laufzeiten erfordern einen Test auf dem installierten Rechner mit erlaubter lokaler Aufnahme.


[English](CHANGELOG.md) | **Deutsch** · [Projektübersicht](../../README.de.md)

## 2.0.0

- Optionaler, authentifizierter Diagnose-Dienst `ops` für Whisper-Verbindung, TTS, Vision, Ollama und – sofern verfügbar – GPU-Werte; keine Speicherung privater Aufnahmen.
- Vision-Schnittstellen `/describe` und `/detect` mit optionaler begrenzter Prioritätswarteschlange und `/capabilities`. Bisheriges sofortiges „busy“-Verhalten bleibt Standard; keine globale GPU-Steuerung.
- Streaming-Qwen-TTS: Textbereinigung, optionales Aussprachewörterbuch, Satzaufteilung und kooperatives `/cancel`.
- Lokales Whisper-WAV-Diagnosewerkzeug für Stille, Übersteuerung und Aufnahmezeit.
- GitHub-CI, Offline-Tests, Docker-Compose-Prüfung und Release-ZIP-Erstellung ohne Zugangsdaten.
- Bestehende APIs und Modellvolumes bleiben erhalten; Hardware-Praxistest nach Installation nötig.

## 1.9.0

### 1.9.0 — Schema-Erweiterung

- Übernommenes Worker-Schema mit geschätzten Erscheinungskategorien, ohne Identitäts- oder Gesichtserkennung. HA akzeptiert weiterhin alte Ergebnisse.

- Authentifizierter `/detect`-Endpunkt mit festem validiertem Personen-/Hund-Schema und grober Einschätzung erwachsen/Kind/unklar. Keine Namen, Identitäten, Geschlechter, freien Prompts oder durch die KI gewählten Aktionen.
- Nutzt den bestehenden Vision-Container, Ollama sowie gewähltes Modell, Kontext und Warmhaltezeit. Vierzehn isolierte Worker-Tests prüfen Erkennung und bisherige Beschreibungen. Freigabe, Sperrzeit und Wiedergabekoordination übernimmt HA-Backend 1.6.0.

## 1.8.0

- Authenticated installed/loaded model status and bounded per-request residency/context for matching HA text/vision settings. Legacy immediate-unload defaults remain compatible; response timings support load-cost diagnosis. No additional service, model download, endpoint exposure or speech changes.

## 1.7.0

- Szenenbeschreibungen dürfen sichtbare Personen allgemein anhand von Kleidung, Position und getragenen Gegenständen beschreiben. Keine Namenszuordnung, Gesichtsvergleiche, sensiblen Zuschreibungen oder Bewegungsverläufe aus einem Einzelbild. Die authentifizierte Einzelbild-API bleibt kompatibel.

## 1.6.0

- Optionaler authentifizierter Einzelbilddienst über vorhandenes Ollama; vier erlaubte Modelle, Qwen3-VL 4B Instruct Standard.
- Feste Beschreibungsmodi, Bildlimits, Metadatenentfernung, eine parallele Vision-Anfrage, Entladen nach Inferenz. Keine Aufnahme oder Bildablage.
- Simulierte API-Tests und PowerShell-Testclient. Sprach-/Textdienste unverändert. GPU und HA-Kameraanbindung am Zielsystem testen.

## 1.5.0
- Authentifizierte Stimmvariantenauswahl 1–9 für vorhandene synthetische Referenzen; fehlende Varianten fallen auf die konfigurierte Referenz zurück. Status im Antwortheader. Keine Uploads oder entfernten Modellneuladungen.
- Lokales prepare_variants.py erstellt weitere Varianten bei gestopptem Streaming-Container. Bestehende Referenzen bleiben erhalten.
- LLM, STT, Schlüssel, Ports und Standardstimme unverändert. Statische/Stubbing-Tests; GPU und Klang am Zielgerät prüfen.

## 1.4.0
- Fixed-Modus: einmalige synthetische VoiceDesign-Referenz im persistenten Modellvolume, wiederverwendet beim Streaming mit Qwen Base.
- Separater Design-Prozess beendet sich vor dem Laden des Base-Modells. Design, styled und fast bleiben verfügbar.
- Optionale 0.6B-Variante, neue Stilbeschreibung oder Varianten-ID erzeugt eine weitere gespeicherte Referenz.
- API, Token, LAN-Port, Audioformat, Whisper und Ollama unverändert; echte CUDA-/Stimmtests ausstehend.

## 1.3.0
- Optionaler lokaler Ollama-GPU-Dienst, ein Modell, eine parallele Anfrage, Kontext 4096 und Entladen bei Leerlauf.
- Authentifizierter LAN-Proxy, bestehender Worker-Schlüssel. Kein direkter Ollama-Port oder Modellverwaltungsendpunkte.
- Qwen3 4B Instruct und HA-Ollama-Einrichtung dokumentiert.
- STT/TTS-Dienste, Image-Tags und Volumes unverändert. Modellinstallation und GPU-Laufzeit prüfen.

## 1.2.0
- Streaming-Stimmprofile fast (0.6B), styled und design (1.7B).
- Konfigurierbare Stimmbeschreibung, unveränderte authentifizierte API und PCM.
- Test-Voice.ps1 erzeugt und spielt lokal WAV. Fast bleibt Standard; GPU-Speicher/Modelllaufzeit prüfen.

## 1.1.1
- Transformers 5.15.1 und qwen-tts-hf 0.1.1.post1 für Encoder-Kompatibilität festgeschrieben und beim Build überprüft.
- Whisper, Qwen, Modellcache und .env unverändert.

## 1.1.0
- Optionales Faster-Qwen-Streaming auf LAN-Port 10502; authentifiziertes PCM und WAV. Whisper und ursprünglicher Qwen-Dienst unverändert.

## 1.0.1
- Compose-GPU-Reservierungen statt gpus-Schlüssel. Konfiguration und Volumes bleiben erhalten.

## 1.0.0
- Optionales GPU-Whisper über Wyoming, separater Qwen3-TTS-Dienst.
- Private LAN-Bindung, Token-Schutz und lokaler WAV-Test.
- Separater Proxmox-TTS-Fallback-Proxy, nicht automatisch aktiviert.
