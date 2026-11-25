# Jarvis GPU Worker 2.2.1

[English](README.md) | **Deutsch** · [Projektübersicht](../README.de.md)

## Installation ohne Tokens (Windows)

Mit **00-Konfiguration.bat** eine `.env` nur mit LAN-IP und Modelloptionen erstellen; mit **01-Installieren.bat** die Whisper- und Qwen-Streaming-Container bauen und starten. **02-Starten.bat** startet die Standarddienste, **03-Neustarten.bat** startet bereits laufende Dienste neu; **04-Verbindungsdaten.bat** erzeugt `GPU-Worker-Verbindungsdaten.txt` mit IP, Ports und Home-Assistant-Einstellungen, **ohne Tokens**. `Setup.ps1` bleibt als kompatibler Einstieg verfügbar. Vorhandene `.env` und Modell-Volumes bleiben unangetastet. Kein Eingriff in Android-App oder Dashboard.

**Sicherheit:** Diese HTTP-Schnittstellen akzeptieren Anfragen ohne zusätzlichen Worker-Schlüssel. Die Docker-Ports werden an die konfigurierte private `LAN_IP` gebunden. In der Windows-Firewall ausschließlich den Home-Assistant- und gegebenenfalls Proxmox-Server zulassen; keine Gastnetze, VPN-Weiterleitung, Reverse-Proxies auf Generator-Ports oder Router-Portfreigaben. Ein öffentlicher HTTPS-Proxy darf ausschließlich kurze, zufällig benannte MP3-Dateien per GET anbieten.



## 2.2.1 – Strukturierte produktive Ring-Bildfolge

Neuer LAN-Endpunkt `POST /describe/sequence` im vorhandenen Vision-Dienst. Standard: zwölf chronologische JPEGs (maximal 768 px Kantenlänge); Detail: vier ausgewählte höher aufgelöste JPEGs (maximal 1024 px). Beide Profile nutzen intern 16384 Kontext-Tokens und dieselbe Vision-Warteschlange. JSON enthält eine kurze deutsche Szenenbeschreibung, dreistufige Merkmale (yes/no/uncertain), Lieferbewertung (likely/uncertain/no_evidence) und Laufzeiten. Kleidung allein bleibt unsicher. Ungültige oder widersprüchliche Modellausgaben werden abgelehnt oder herabgestuft. Kein Zustellnachweis. /describe, /detect und /benchmark/sequence bleiben kompatibel.

Vorhandene .env und Modellvolumes beibehalten. Nur Vision neu bauen: `docker compose --profile vision up -d --build --no-deps vision`. Danach capabilities und `docker compose exec -T vision python -m unittest -v test_server test_sequence_benchmark test_priority_gate` prüfen. Das ältere HA-Overlay 1.6.1 nicht über ein bereits individuell angepasstes Backend kopieren; die HA-Umstellung auf den strukturierten Endpunkt erfolgt separat nach Installation. Kein zusätzlicher Container und bei vorhandenem Qwen3-VL kein Modelldownload nötig.

### Home Assistant (Backend 1.6.2)

Die strukturierte Ring-Auswertung ist im aktuellen Integrationsstand enthalten. Übernimm die Integration als Ganzes bzw. das CI-Overlay `jarvis-ring-backend-1.6.2` für kompatible 1.6.x-Installationen. Die normale Tablet-Einzelbildanalyse bleibt unverändert. `describe_camera` mit `mode: ring_video` verwendet zwölf Bilder; bei unsicherem Lieferhinweis vier höher aufgelöste Bilder, bei Fehlern die bisherigen Rückfallwege. Automatische A/B-Tests laufen nicht mehr im Produktionspfad. Beispielkonfiguration und Einrichtung: [Ring-Lieferhinweise](../homeassistant/examples/RING.de.md).

## 2.0.0 – Abschluss und Betrieb

**Diagnose:** Das optionale Profil `ops` stellt unter Port **10504** im
privaten LAN die LAN-Endpunkte `GET /health`,
`GET /status` und `GET /selftest` bereit. Start:
`docker compose --profile ops up -d --build ops`.
Die Prüfung zeigt Dienstverfügbarkeit und bei
verfügbarem `nvidia-smi` GPU-Auslastung/Speicher. Sie führt **keine**
automatischen KI-Anfragen aus. Nicht gestartete Compose-Profile erscheinen
als nicht verfügbar.

**Vision-Warteschlange:** `/describe` und `/detect` akzeptieren optional
`priority: "interactive" | "background"` und `wait_ms: 0..20000`.
Maximal sechs wartende Anfragen; ohne diese Felder bleibt das bisherige
sofortige „busy“-Verhalten erhalten. Die Priorisierung gilt **nur innerhalb
des Vision-Dienstes**, nicht global für Whisper, Ollama und TTS.
`GET /capabilities` listet die Schnittstellen.

**Sprachausgabe:** Bereinigung einfacher Textformatierungen über
`STREAM_TEXT_CLEANUP=1` (Standard). Optionales Wörterbuch
`STREAM_PRONUNCIATION` als JSON, z. B.
`{"kWh":"Kilowattstunden"}`, sowie `STREAM_SPEECH_SPLIT=1` für die
Satzaufteilung längerer Antworten. `POST /cancel` (nur LAN)
bricht Streaming kooperativ zwischen Audioblöcken ab; das Tablet muss
laufendes Audio zusätzlich selbst stoppen. Die alten TTS-Endpunkte
bleiben unverändert nutzbar.

**Whisper-Werkzeug:** `python tools/check_audio.py aufnahme.wav` untersucht
eine lokale 16-Bit-PCM-WAV-Datei auf Stille, Übersteuerung und zu kurze
Aufnahmen. Es lädt oder speichert nichts. Die VAD- und End-of-Speech-
Einstellungen bleiben bei Home Assistant bzw. dem Sprachclient.

**Freigabeprüfung:** `python check_release.py` kontrolliert VERSION,
Dokumentation und Docker-Tags. Mit
`python check_release.py --package ../jarvis-gpu-worker-2.0.0.zip`
entsteht ein Release-ZIP ohne `.env`, Schlüssel, Testaudio oder Cachedateien.
Vorhandene `.env` und Modell-Volumes unbedingt behalten. Vor dem Betrieb
Docker-Konfiguration prüfen und nur benötigte Container neu bauen.

**Grenzen:** Eine zentrale GPU-Priorisierung über alle getrennten Container
ist noch nicht umgesetzt. Die neuen Dienste brauchen weiterhin einen
echten Praxistest auf dem GPU-Rechner.



> **Schema-Update zu Worker 1.9.0:** Der lokale `/detect`-Endpunkt liefert zusätzlich `genders` mit den groben, unsicheren Erscheinungskategorien `man`, `woman`, `unknown`. Keine tatsächliche Geschlechts- oder Identitätsfeststellung. Vorhandene `.env` und Modellvolumes beibehalten, nur Vision neu bauen; HA-Backend gemeinsam aktualisieren. [HA-Automationen](../docs/ha-automations.md).

Der bestehende Vision-Container bietet zusätzlich die ausdrücklich aktivierbare strukturierte Bewegungsauswertung. [Proaktive Einrichtung](../docs/echo-relay-dashboard.md#bewegungsgesteuerte-aktionen). Es wird kein weiterer Container und kein zusätzliches Modell benötigt.

Das Profil `vision` ergänzt Ollama um ausdrücklich angeforderte Einzelbildbeschreibungen; Qwen3 4B Instruct, Whisper und TTS bleiben unverändert. Standard: `qwen3-vl:4b-instruct` (Ollama >= 0.12.7); Alternativen: `qwen3-vl:2b-instruct`, `qwen3-vl:8b-instruct`, `gemma3:4b`. Update am GPU-PC, nicht auf Proxmox: bestehende `.env` und Volumes behalten.

```powershell
docker compose config --quiet
docker compose --profile llm --profile vision up -d --build vision
docker compose exec ollama ollama pull qwen3-vl:4b-instruct
docker compose exec vision python -m unittest -v test_server
```

Test mit einem eigenen unkritischen JPEG/PNG: `.\Test-Vision.ps1 -ImagePath C:\Bilder\test.png`. Anderes Modell lokal pullen, `VISION_MODEL` in .env setzen und `docker compose --profile vision up -d --no-deps vision` ausführen. Textmodell bleibt erhalten, Ollama lädt maximal ein Modell gleichzeitig, Vision fordert keep_alive 0 an. Modellwechsel können Zeit kosten; VRAM mit `nvidia-smi` prüfen.

API: GET `/health` und POST `/describe` auf Privat-LAN-Port 10503, JSON `{"image":"<base64 JPEG/PNG>","mode":"scene"}`; Modi scene, objects, object_in_hand; optional model aus obiger Liste. Maximal 2 MiB/12 MP, intern auf 1280 px verkleinert, Metadaten entfernt. Antwort description, model, mode, limitation. Keine URL-/Stream-Aufnahme, freie Prompts oder Gerätebefehle, allgemeine Beschreibungen sichtbarer Personen, Kleidung und Gegenstände, keine Namenszuordnung oder Gesichtserkennung oder persistente Bilder. Nur Bilder, deren Verwendung erlaubt ist. Firewall auf HA beschränken; HTTP unverschlüsselt; keine Router-Portfreigabe. HA-Kameraauswahl und Android-Kameraübertragung sind über die Echo-Relay-Integration verfügbar. Beschreibungen können falsch sein. Mit `docker compose --profile vision stop vision` deaktivieren, keine Volumes löschen.

---

# Jarvis GPU Worker v1.5.0 – Stimmenwahl

Vorhandene `.env` unverändert behalten, besonders `STREAM_VOICE_STYLE` und `STREAM_VOICE_VARIANT=1`. Update in den vorhandenen Ordner kopieren.

```powershell
docker compose config --quiet
docker compose --profile stream up -d --build --no-deps qwen-stream
```

Die bestehende feste Stimme bleibt erhalten. Die HA-Auswahl kann bereits vorbereitete Varianten 1–9 für dieselbe Stimmbeschreibung verwenden. Falls eine Variante nicht existiert, wird die bestehende Standardstimme verwendet; das wird im Antwortheader gemeldet. Keine neuen Stimmen werden während einer Anfrage erzeugt. Identische gecachte HA-Antworten können alte Stimmen enthalten.

Optional zwei weitere Varianten vorbereiten (währenddessen Piper als Reserve; bei knappem VRAM vorher laufende LLM-Anfragen abschließen).

```powershell
docker compose --profile stream stop qwen-stream
docker compose --profile stream run --rm --no-deps qwen-stream python /app/prepare_variants.py 2 3
docker compose --profile stream up -d --no-deps qwen-stream
```

Bei Fehlern den Streaming-Container mit dem letzten Befehl wieder starten. Keine Volumes löschen. Die Vorbereitung arbeitet lokal mit synthetischen Stimmen; keine fremden Sprachaufnahmen. Das Update braucht keine neue Portfreigabe. GPU-Laufzeit und Stimmenwechsel am Zielgerät testen.


---

# Jarvis GPU Worker v1.4.0 – Feste synthetische Stimme

Bestehende `.env` behalten. ZIP-Inhalt in den bisherigen Ordner kopieren. In `.env` die bestehende Zeile `STREAM_VOICE_MODE=design` durch `STREAM_VOICE_MODE=fixed` ersetzen; die bestehende `STREAM_VOICE_STYLE`-Zeile unverändert lassen. Optional `STREAM_VOICE_VARIANT=1` (Standard), `STREAM_FIXED_MODEL_SIZE=1.7B` (Standard) oder `0.6B` für kleineren Speicherbedarf.

```powershell
docker compose config --quiet
docker compose --profile stream up -d --build --no-deps qwen-stream
docker compose --profile stream logs -f qwen-stream
```

Beim ersten Start erzeugt VoiceDesign eine neue synthetische Referenz und speichert sie im bestehenden Volume `qwen-data` unter `/models/jarvis-voices/<voice_id>.wav`. Das Design-Modell läuft in einem separaten Prozess und wird vor dem Laden von Base beendet. Base benötigt einen zusätzlichen Modelldownload. Dieselbe Beschreibung und Varianten-ID verwenden künftig dieselbe Referenz auch nach Neustarts. Eine andere Varianten-ID (z. B. `2`) erstellt eine neue Referenz; zurück auf `1` wählt die alte. Die Stimme ist eine neu erzeugte, eigenständige Stimme, nicht exakt die letzte Design-Ausgabe. Nur synthetische Referenzen, keine fremden Sprachaufnahmen. Klang und Prosodie können weiterhin etwas variieren. Sobald `Faster Qwen ready on port 10502` erscheint, `Test-Voice.ps1` und `Test-Stream.ps1` ausführen; die Ergebnisse verschiedener neuer Sätze vergleichen. HA kann alte identische Texte zwischenspeichern. Keine Änderungen in HA nötig. Wenn VRAM knapp ist, auf 0.6B Base oder den vorherigen Modus `design` bzw. `fast` zurückwechseln und nur den Streaming-Container neu erstellen. Keine Volumes löschen. GPU-Laufzeit nicht hier verifiziert.


Quellen: https://github.com/QwenLM/Qwen3-TTS#voice-design-then-clone · https://github.com/andimarafioti/faster-qwen3-tts

---

# Jarvis GPU Worker v1.3.0 – Lokales LLM

## Ollama zusätzlich starten

Dateien in den bisherigen Ordner kopieren und die bestehende `.env` unverändert behalten. Whisper und Qwen-Streaming bleiben unverändert. Nur ein TTS-Modell gleichzeitig betreiben. Ollama verwendet dieselbe RTX und hat mit VoiceDesign möglicherweise nicht genug VRAM für vollständige GPU-Auslagerung. Prüfe den gemeinsamen Betrieb; kein Leistungsversprechen.

```powershell
docker compose config --quiet
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
docker compose exec ollama ollama run qwen3:4b-instruct "Erklaere in einem kurzen deutschen Satz, warum der Himmel blau ist."
docker compose exec ollama ollama ps
nvidia-smi
```

Die Modelle bleiben im benannten Volume. Nicht `down -v` verwenden. Der LAN-Gateway lauscht auf `${LAN_IP}:11434`; Ollama selbst ist nicht veröffentlicht. Der Gateway benötigt keinen zusätzlichen Token; er lässt nur Inferenz- und Abfrage-Endpunkte zu. Zugriff per Firewall auf HA begrenzen. Modell-Downloads nur über `docker compose exec ollama ollama pull ...`. HTTP ist nicht verschlüsselt: nur vertrauenswürdiges LAN, Windows-Firewall auf Home-Assistant-Host beschränken, keine Router-Portfreigabe. Kein Cloud-Modell. Ollama und Nginx werden über ihre offiziellen Tags bezogen; Updates bewusst testen.

Home Assistant: Ollama-Integration mit URL `http://<LAN_IP>:11434` hinzufügen. Gesprächsagent „Jarvis KI“, Modell `qwen3:4b-instruct`, Kontext 4096, Max history 6, Keep alive 0, Denken aus. AI tools zunächst keine. Anleitung: präzise, kurze deutsche Antworten, keine behaupteten Aktionen oder erfundenen Hausdaten. Im Assist-Assistenten bevorzugt lokale Befehle verarbeiten; erst nach Test auf KI-Agent umstellen. Ohne PC bleiben native lokale HA-Intents sinnvoll, freie Wissensfragen sind dann nicht verfügbar. HA-Integration und Gateway sind noch nicht praktisch gemeinsam geprüft.

Bei Speicherproblemen `docker compose --profile llm stop ollama-gateway ollama`. Whisper und TTS bleiben an. Teste ggf. einen kleineren LLM-Tag oder TTS fast/styled statt design. Keine Datenvolumes löschen. HA-Standardagent bleibt jederzeit als Rückfall nutzbar.


Dokumentation: https://docs.ollama.com/docker · https://www.home-assistant.io/integrations/ollama/

---

# Jarvis GPU Worker v1.2.0 – Stimmprofile

Bestehende `.env` behalten. Dateien überschreiben. Der Standard `fast` bleibt unverändert. Für eine neue synthetische Stimme in `.env` einmal `STREAM_VOICE_MODE=design` ergänzen (alternativ `styled` für Ryan mit Stilvorgabe oder `fast` für den bisherigen Modus). Optional `STREAM_VOICE_STYLE=...` als einzeilige Beschreibung. Nicht den Schlüssel teilen. Nur ein TTS-Modell gleichzeitig laden. `docker compose --profile stream up -d --build --no-deps qwen-stream` erstellt nur den Streaming-Container neu. `./Test-Voice.ps1` lokal abspielen; `./Test-Stream.ps1` misst Latenzen. Bei Speicherfehlern `STREAM_VOICE_MODE=fast` setzen und denselben Compose-Befehl erneut ausführen. Modelle bleiben im Volume. VoiceDesign kann zwischen Anfragen leicht variieren. Neue Profile noch nicht auf der Ziel-GPU geprüft. Die HA-API bleibt kompatibel. Bei gleichlautenden Antworten kann HA altes Audio aus dem Cache verwenden.


---

# Jarvis GPU Worker 1.1.1

Optionaler GPU-Worker für Windows 10/11, kompatible NVIDIA-GPU und Docker Desktop mit WSL2/Linux-Containern. Der vorhandene Proxmox-Sprachserver bleibt unverändert. Dieses Paket enthält keine Modelle; die Images und Gewichte werden erst beim Aufbau heruntergeladen. Plane mehrere zehn GB freien SSD-Speicher ein. Der Docker-Build und die GPU-Inferenz konnten nicht auf deiner Hardware ausgeführt werden.

## Update von 1.0.0
Nur `compose.yaml` im vorhandenen Ordner ersetzen. Die vorhandene `.env` nicht ändern oder neu erzeugen. `docker compose config --quiet` zur Prüfung ausführen; danach Whisper wie bisher starten. GPU-Reservierungen sind nun unter `deploy.resources.reservations.devices` definiert.

## Installation am Windows-Hauptrechner
1. Aktuellen NVIDIA-Treiber und Docker Desktop (WSL2-Backend, Linux-Container) installieren. Docker öffnen. Netzwerkprofil Privat; nur an das vertrauenswürdige Heimnetz anbinden.
2. ZIP entpacken. Im entpackten Ordner PowerShell öffnen. `nvidia-smi` und `docker version` prüfen. `powershell -NoProfile -File .\Setup.ps1` ausführen. Falls die Skriptausführung blockiert ist, die Datei erst prüfen und die Anweisungen daraus in PowerShell ausführen; keine systemweite Richtlinie lockern. Die lokale IPv4-Adresse des Hauptrechners auswählen. `.env` nicht teilen. IP per DHCP-Reservierung stabil halten.
3. Windows-Firewall: TCP 10300 ausschließlich von Home Assistant erlauben; TCP 10501 ausschließlich von CPU-Sprachserver (eigene LAN-IP) erlauben. Für den lokalen Test ist keine Freigabe für andere Geräte nötig. Prüfe auch etwaige bestehende Docker-Firewallregeln. Keine Router-Portweiterleitungen. Wyoming hat selbst keine Authentifizierung.
4. Whisper starten: `docker compose up -d --build whisper`. `docker compose logs -f whisper` (Strg+C beendet nur die Logansicht). Erstmaliger Image-Build und Modelldownload können aufwendig sein. Nach Bereitschaft Home Assistant Wyoming mit Windows-IP, Port 10300 verbinden; neue STT-Entität ermitteln. In der Sprachzentrale als STT-Zusatzrechner eintragen, Profil Automatisch. Das bestehende Whisper Tiny bleibt Reserve. Die Umschaltung bei abgeschaltetem PC separat testen.
5. Qwen separat starten: `docker compose --profile tts up -d --build qwen`. `docker compose --profile tts logs -f qwen`. Erst nach "Qwen ready" den Test mit `powershell -NoProfile -File .\Test-Qwen.ps1` durchführen. WAV wird lokal abgespielt. Der Test benutzt die Modellstimme Ryan, die auch Deutsch sprechen kann; sie ist nicht primär deutsch trainiert. Die 1.7B-VoiceDesign-Variante ist optional, nicht der Startwert. Beide Dienste können um 12 GB VRAM konkurrieren. Erst einzeln testen, dann gemeinsam. Bei OOM `docker compose --profile tts stop qwen` oder das andere Modell stoppen. LM Studio in dieser Version noch nicht enthalten.
6. Stoppen: `docker compose --profile tts down` (ohne `-v`, damit Modelle erhalten bleiben). Erneuter Start: `docker compose up -d whisper` bzw. `docker compose --profile tts up -d qwen`. 

## Proxmox-TTS-Router (vorbereitet, noch nicht einschalten)
`proxmox/tts_router.py` ist ein eigenständiger Piper-kompatibler WAV-Proxy auf 127.0.0.1:5002. Im Modus `auto` versucht er Qwen über die private Windows-IP bei Nichterreichbarkeit oder Fehler Piper auf 127.0.0.1:5000. keine öffentliche Freigabe. Er schreibt keine Audiodateien. Die bestehende Piper-API übernimmt weiterhin die MP3-Erzeugung und begrenzte Bereitstellung. Nur nichtvertrauliche Ansagen über Alexa nutzen.

**Nicht den existierenden Piper-Dienst oder seine Ports umstellen.** Vor Einbau muss die tatsächliche URL-Konfiguration in `/opt/piper/api.py` geprüft werden. Bitte nur die betreffenden Zeilen (ohne Zugangsdaten) teilen: `grep -nE '127\.0\.0\.1:5000|localhost:5000|/synthesize|PIPER_URL' /opt/piper/api.py`. Erst danach richten wir den Proxy-Dienst mit eingeschränktem Benutzer, Konfigurationsdatei und Modus `piper` ein, testen ihn, und ändern genau die Piper-API-Zieladresse. Rückfall auf Piper lässt sich durch Modus `piper` bzw. Zurücksetzen der Zieladresse erzwingen. Kein HA-Neustart erforderlich, solange nur dieses Backend geändert wird.

Quellen: https://github.com/OHF-Voice/wyoming-faster-whisper · https://github.com/QwenLM/Qwen3-TTS · https://docs.docker.com/desktop/features/gpu/

## v1.1.0: Faster Qwen (experimentell)

Dateien in den bestehenden Installationsordner kopieren, `.env` unverändert lassen. Docker Desktop starten. Den alten Qwen-Dienst stoppen, um VRAM zu sparen; Whisper bleibt an.

```powershell
docker compose stop qwen
docker compose --profile stream up -d --build qwen-stream
docker compose logs -f qwen-stream
```

Port 10502 nur vom vertrauenswürdigen lokalen Home Assistant erreichbar machen; kein Internet-Portforwarding. `Test-Stream.ps1` misst Zeit bis HTTP-Antwort/erste Bytes; Container-Log misst erste generierte PCM-Daten. Erster Durchlauf kann CUDA-Graph-Capture enthalten. Danach erneut testen. Rückkehr: `docker compose stop qwen-stream; docker compose --profile tts up -d qwen`. Die GPU- und Docker-Laufzeit sind auf Zielhardware noch nicht getestet. Die native Android-Wiedergabe muss separat geprüft werden.

## v1.1.1: Kompatibilitätsfix

Bei `property 'upsample' ... has no setter` nur die Streaming-Abhängigkeiten korrigieren. Transformers 5.15.1 und qwen-tts-hf 0.1.1.post1 sind fest vorgegeben. Kopiere die Dateien aus dem ZIP in den vorhandenen Installationsordner (bestehende .env beibehalten).

```powershell
docker compose --profile stream stop qwen-stream
docker compose --profile stream up -d --build --no-deps qwen-stream
docker compose --profile stream logs -f qwen-stream
```

Nach `Faster Qwen ready on port 10502` mit Strg+C die Logansicht beenden und `./Test-Stream.ps1` ausführen. Keine Volumes löschen. Keine Zugangsdaten teilen. Der Fix wurde statisch geprüft, nicht auf einer GPU ausgeführt.

Referenz: https://github.com/andimarafioti/faster-qwen3-tts/blob/main/README.md


## Jarvis-Modelleinstellungen (1.8.0)

Mit Jarvis Tablet Audio 1.5.0 lassen sich unter **KI & Leistung** installierte Text- und Bildmodelle, Kontext (2048/4096/8192 Tokens) und Warmhaltezeit (0/60/120/300/600 Sekunden) zentral wählen. Für gemeinsamen Betrieb beide Modelle auf `qwen3-vl:4b-instruct` setzen; getrennt Qwen3 4B Instruct als Textmodell und Qwen3-VL 4B Instruct als Bildmodell wählen. Ollama lädt höchstens ein Modell und verarbeitet eine Anfrage gleichzeitig. GPU-Speicherbedarf gemeinsam mit STT und TTS prüfen. Keine automatischen Downloads oder zusätzlichen Dienste. Ältere Vision-Aufrufe entladen standardmäßig sofort.

Der LAN-Aufruf `GET /runtime` meldet ausschließlich unterstützte installierte und geladene Modelle. `POST /describe` erlaubt begrenzte Werte für `keep_alive` und `num_ctx` und liefert Zeitmessungen. HA übergibt gespeicherte Einstellungen und aktualisiert den bestehenden Ollama-Gesprächsagenten, ohne Prompts, Werkzeuge oder Verlauf zu verändern. Reine Kameraanzeigen umgehen beide Modelle. Änderungen gelten ab der nächsten Anfrage; die erste Anfrage nach Leerlauf kann länger dauern. Bestehende `.env` und Volumes erhalten; beim Update nur Vision neu bauen. Kein APK-Update erforderlich.
