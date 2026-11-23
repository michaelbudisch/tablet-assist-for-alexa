**Deutsch** | [English](README.en.md) · [Installation](../docs/worker.md)

# Jarvis GPU Worker v1.9.0 – Optionales Visionmodell

> **Schema-Update zu Worker 1.9.0:** Der lokale `/detect`-Endpunkt liefert zusätzlich `genders` mit den groben, unsicheren Erscheinungskategorien `man`, `woman`, `unknown`. Keine tatsächliche Geschlechts- oder Identitätsfeststellung. Vorhandene `.env` und Modellvolumes beibehalten, nur Vision neu bauen; HA-Backend gemeinsam aktualisieren. [HA-Automationen](../docs/ha-automations.md).

Der bestehende Vision-Container bietet zusätzlich die ausdrücklich aktivierbare strukturierte Bewegungsauswertung. [Proaktive Einrichtung](../docs/echo-relay-dashboard.md#bewegungsgesteuerte-aktionen--motion-triggered-actions). Es wird kein weiterer Container und kein zusätzliches Modell benötigt.

Das Profil `vision` ergänzt Ollama um ausdrücklich angeforderte Einzelbildbeschreibungen; Qwen3 4B Instruct, Whisper und TTS bleiben unverändert. Standard: `qwen3-vl:4b-instruct` (Ollama >= 0.12.7); Alternativen: `qwen3-vl:2b-instruct`, `qwen3-vl:8b-instruct`, `gemma3:4b`. Update am GPU-PC, nicht auf Proxmox: bestehende `.env` und Volumes behalten.

```powershell
docker compose config --quiet
docker compose --profile llm --profile vision up -d --build vision
docker compose exec ollama ollama pull qwen3-vl:4b-instruct
docker compose exec vision python -m unittest -v test_server
```

Test mit einem eigenen unkritischen JPEG/PNG: `.\Test-Vision.ps1 -ImagePath C:\Bilder\test.png`. Anderes Modell lokal pullen, `VISION_MODEL` in .env setzen und `docker compose --profile vision up -d --no-deps vision` ausführen. Textmodell bleibt erhalten, Ollama lädt maximal ein Modell gleichzeitig, Vision fordert keep_alive 0 an. Modellwechsel können Zeit kosten; VRAM mit `nvidia-smi` prüfen.

API: GET `/health` und POST `/describe` auf Privat-LAN-Port 10503, Header `X-API-Key` mit bestehendem Worker-Token. JSON `{"image":"<base64 JPEG/PNG>","mode":"scene"}`; Modi scene, objects, object_in_hand; optional model aus obiger Liste. Maximal 2 MiB/12 MP, intern auf 1280 px verkleinert, Metadaten entfernt. Antwort description, model, mode, limitation. Keine URL-/Stream-Aufnahme, freie Prompts oder Gerätebefehle, allgemeine Beschreibungen sichtbarer Personen, Kleidung und Gegenstände, keine Namenszuordnung oder Gesichtserkennung oder persistente Bilder. Nur Bilder, deren Verwendung erlaubt ist. Firewall auf HA beschränken; HTTP unverschlüsselt; keine Router-Portfreigabe. HA-Kameraauswahl und Android-Kameraübertragung sind über die Echo-Relay-Integration verfügbar. Beschreibungen können falsch sein. Mit `docker compose --profile vision stop vision` deaktivieren, keine Volumes löschen.

---

# Jarvis GPU Worker v1.5.0 – Stimmenwahl / Voice selection

DE: Vorhandene `.env` unverändert behalten, besonders `STREAM_VOICE_STYLE` und `STREAM_VOICE_VARIANT=1`. Update in den vorhandenen Ordner kopieren.

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

Bei Fehlern den Streaming-Container mit dem letzten Befehl wieder starten. Keine Volumes löschen. Die Vorbereitung arbeitet lokal mit synthetischen Stimmen; keine fremden Sprachaufnahmen. Das Update braucht keine neue Portfreigabe. API-Key nicht teilen. GPU-Laufzeit und Stimmenwechsel am Zielgerät testen.

EN: Keep the existing .env and model volume. Rebuild the streaming service only. The optional authenticated voice_variant field chooses a previously prepared original synthetic reference 1–9 for the current style. Unknown variants use the configured default, with status in the response headers. Create extra variants manually using the commands above; stop the stream service first. No new ports or remote voice creation endpoints. GPU/voice tests required.

---

# Jarvis GPU Worker v1.4.0 – Feste synthetische Stimme / Fixed synthetic voice

DE: Bestehende `.env` behalten. ZIP-Inhalt in den bisherigen Ordner kopieren. In `.env` die bestehende Zeile `STREAM_VOICE_MODE=design` durch `STREAM_VOICE_MODE=fixed` ersetzen; die bestehende `STREAM_VOICE_STYLE`-Zeile unverändert lassen. Optional `STREAM_VOICE_VARIANT=1` (Standard), `STREAM_FIXED_MODEL_SIZE=1.7B` (Standard) oder `0.6B` für kleineren Speicherbedarf.

```powershell
docker compose config --quiet
docker compose --profile stream up -d --build --no-deps qwen-stream
docker compose --profile stream logs -f qwen-stream
```

Beim ersten Start erzeugt VoiceDesign eine neue synthetische Referenz und speichert sie im bestehenden Volume `qwen-data` unter `/models/jarvis-voices/<voice_id>.wav`. Das Design-Modell läuft in einem separaten Prozess und wird vor dem Laden von Base beendet. Base benötigt einen zusätzlichen Modelldownload. Dieselbe Beschreibung und Varianten-ID verwenden künftig dieselbe Referenz auch nach Neustarts. Eine andere Varianten-ID (z. B. `2`) erstellt eine neue Referenz; zurück auf `1` wählt die alte. Die Stimme ist eine neu erzeugte, eigenständige Stimme, nicht exakt die letzte Design-Ausgabe. Nur synthetische Referenzen, keine fremden Sprachaufnahmen. Klang und Prosodie können weiterhin etwas variieren. Sobald `Faster Qwen ready on port 10502` erscheint, `Test-Voice.ps1` und `Test-Stream.ps1` ausführen; die Ergebnisse verschiedener neuer Sätze vergleichen. HA kann alte identische Texte zwischenspeichern. Keine Änderungen in HA nötig. Wenn VRAM knapp ist, auf 0.6B Base oder den vorherigen Modus `design` bzw. `fast` zurückwechseln und nur den Streaming-Container neu erstellen. Keine Volumes löschen. GPU-Laufzeit nicht hier verifiziert.

EN: Keep `.env`, replace the existing mode with `fixed`, retain the voice description. A one-time original synthetic reference is persisted in the existing model volume and reused via streaming Base inference. Change the variant to generate another reference; the previous one is retained. Optional 0.6B Base reduces memory. No HA/API changes. GPU and voice tests remain necessary. See the commands above.

References: https://github.com/QwenLM/Qwen3-TTS#voice-design-then-clone · https://github.com/andimarafioti/faster-qwen3-tts

---

# Jarvis GPU Worker v1.3.0 – Lokales LLM / Local LLM

## DE: Ollama zusätzlich starten

Dateien in den bisherigen Ordner kopieren und die bestehende `.env` unverändert behalten. Whisper und Qwen-Streaming bleiben unverändert. Nur ein TTS-Modell gleichzeitig betreiben. Ollama verwendet dieselbe RTX und hat mit VoiceDesign möglicherweise nicht genug VRAM für vollständige GPU-Auslagerung. Prüfe den gemeinsamen Betrieb; kein Leistungsversprechen.

```powershell
docker compose config --quiet
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
docker compose exec ollama ollama run qwen3:4b-instruct "Erklaere in einem kurzen deutschen Satz, warum der Himmel blau ist."
docker compose exec ollama ollama ps
nvidia-smi
```

Die Modelle bleiben im benannten Volume. Nicht `down -v` verwenden. Der Auth-Gateway lauscht auf `${LAN_IP}:11434`; Ollama selbst ist nicht veröffentlicht. Der Gateway verlangt `Authorization: Bearer <vorhandener JARVIS_TTS_TOKEN>`; er lässt nur Inferenz- und Abfrage-Endpunkte zu. Modell-Downloads nur über `docker compose exec ollama ollama pull ...`. Den vorhandenen Token ausschließlich in der HA-Integrationsmaske eintragen, nicht in einen Chat, Screenshot oder öffentliche Logs. HTTP ist nicht verschlüsselt: nur vertrauenswürdiges LAN, Windows-Firewall auf Home-Assistant-Host beschränken, keine Router-Portfreigabe. Kein Cloud-Modell. Ollama und Nginx werden über ihre offiziellen Tags bezogen; Updates bewusst testen.

Home Assistant: Ollama-Integration mit URL `http://<LAN_IP>:11434` hinzufügen. API-Key = bestehender Worker-Token. Gesprächsagent „Jarvis KI“, Modell `qwen3:4b-instruct`, Kontext 4096, Max history 6, Keep alive 0, Denken aus. AI tools zunächst keine. Anleitung: präzise, kurze deutsche Antworten, keine behaupteten Aktionen oder erfundenen Hausdaten. Im Assist-Assistenten bevorzugt lokale Befehle verarbeiten; erst nach Test auf KI-Agent umstellen. Ohne PC bleiben native lokale HA-Intents sinnvoll, freie Wissensfragen sind dann nicht verfügbar. HA-Integration und Gateway sind noch nicht praktisch gemeinsam geprüft.

Bei Speicherproblemen `docker compose --profile llm stop ollama-gateway ollama`. Whisper und TTS bleiben an. Teste ggf. einen kleineren LLM-Tag oder TTS fast/styled statt design. Keine Datenvolumes löschen. HA-Standardagent bleibt jederzeit als Rückfall nutzbar.

## EN: Add local Ollama

Copy files into the existing worker folder; retain `.env`. Start the `llm` profile with the commands above, pull the local 4B instruct model, and test VRAM with `ollama ps` and `nvidia-smi`. The authenticated proxy uses the existing worker token; configure it only in HA's Ollama setup dialog. Keep the API on a trusted LAN, restrict firewall access to HA, never forward the port to the Internet. Native HA local-intent priority and the AI agent must be tested before switching the existing pipeline. No cloud AI or extra device-control tools. Stop only the two `llm` services to revert. Existing TTS/STT files are unchanged.

Docs: https://docs.ollama.com/docker · https://www.home-assistant.io/integrations/ollama/

---

# Jarvis GPU Worker v1.2.0 – Voice profiles

DE: Bestehende `.env` behalten. Dateien überschreiben. Der Standard `fast` bleibt unverändert. Für eine neue synthetische Stimme in `.env` einmal `STREAM_VOICE_MODE=design` ergänzen (alternativ `styled` für Ryan mit Stilvorgabe oder `fast` für den bisherigen Modus). Optional `STREAM_VOICE_STYLE=...` als einzeilige Beschreibung. Nicht den Schlüssel teilen. Nur ein TTS-Modell gleichzeitig laden. `docker compose --profile stream up -d --build --no-deps qwen-stream` erstellt nur den Streaming-Container neu. `./Test-Voice.ps1` lokal abspielen; `./Test-Stream.ps1` misst Latenzen. Bei Speicherfehlern `STREAM_VOICE_MODE=fast` setzen und denselben Compose-Befehl erneut ausführen. Modelle bleiben im Volume. VoiceDesign kann zwischen Anfragen leicht variieren. Neue Profile noch nicht auf der Ziel-GPU geprüft. Die HA-API bleibt kompatibel. Bei gleichlautenden Antworten kann HA altes Audio aus dem Cache verwenden.

EN: Keep the existing `.env`. Copy files over. Default `fast` retains the proven 0.6B model. Set `STREAM_VOICE_MODE=design` for an original synthetic voice or `styled` for a preset with instructions. Optional one-line `STREAM_VOICE_STYLE`. Keep the key private. Run only one TTS model at a time; recreate only qwen-stream using the command above. Test locally; revert to `fast` if VRAM is insufficient. New profiles require actual GPU testing; API unchanged. VoiceDesign can vary between requests; HA may cache identical responses.

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
`proxmox/tts_router.py` ist ein eigenständiger Piper-kompatibler WAV-Proxy auf 127.0.0.1:5002. Im Modus `auto` versucht er Qwen über die private Windows-IP und den Token aus `.env`, bei Nichterreichbarkeit oder Fehler Piper auf 127.0.0.1:5000. Die Tokenübertragung geschieht nur im vertrauenswürdigen LAN (HTTP ohne TLS); keine öffentliche Freigabe. Er schreibt keine Audiodateien. Die bestehende Piper-API übernimmt weiterhin die MP3-Erzeugung und begrenzte Bereitstellung. Nur nichtvertrauliche Ansagen über Alexa nutzen.

**Nicht den existierenden Piper-Dienst oder seine Ports umstellen.** Vor Einbau muss die tatsächliche URL-Konfiguration in `/opt/piper/api.py` geprüft werden. Bitte nur die betreffenden Zeilen (ohne Zugangsdaten) teilen: `grep -nE '127\.0\.0\.1:5000|localhost:5000|/synthesize|PIPER_URL' /opt/piper/api.py`. Erst danach richten wir den Proxy-Dienst mit eingeschränktem Benutzer, Konfigurationsdatei und Modus `piper` ein, testen ihn, und ändern genau die Piper-API-Zieladresse. Rückfall auf Piper lässt sich durch Modus `piper` bzw. Zurücksetzen der Zieladresse erzwingen. Kein HA-Neustart erforderlich, solange nur dieses Backend geändert wird.

Quellen: https://github.com/OHF-Voice/wyoming-faster-whisper · https://github.com/QwenLM/Qwen3-TTS · https://docs.docker.com/desktop/features/gpu/

## v1.1.0: Faster Qwen (experimentell)

Dateien in den bestehenden Installationsordner kopieren, `.env` unverändert lassen. Docker Desktop starten. Den alten Qwen-Dienst stoppen, um VRAM zu sparen; Whisper bleibt an.

```powershell
docker compose stop qwen
docker compose --profile stream up -d --build qwen-stream
docker compose logs -f qwen-stream
```

Port 10502 nur vom vertrauenswürdigen lokalen Home Assistant erreichbar machen; kein Internet-Portforwarding. Der bestehende zufällige API-Key wird weiter genutzt; nie in Chat oder Logs senden. `Test-Stream.ps1` misst Zeit bis HTTP-Antwort/erste Bytes; Container-Log misst erste generierte PCM-Daten. Erster Durchlauf kann CUDA-Graph-Capture enthalten. Danach erneut testen. Rückkehr: `docker compose stop qwen-stream; docker compose --profile tts up -d qwen`. Die GPU- und Docker-Laufzeit sind auf Zielhardware noch nicht getestet. Die native Android-Wiedergabe muss separat geprüft werden.

## v1.1.1: Kompatibilitätsfix

Bei `property 'upsample' ... has no setter` nur die Streaming-Abhängigkeiten korrigieren. Transformers 5.15.1 und qwen-tts-hf 0.1.1.post1 sind fest vorgegeben. Kopiere die Dateien aus dem ZIP in den vorhandenen Installationsordner (bestehende .env beibehalten).

```powershell
docker compose --profile stream stop qwen-stream
docker compose --profile stream up -d --build --no-deps qwen-stream
docker compose --profile stream logs -f qwen-stream
```

Nach `Faster Qwen ready on port 10502` mit Strg+C die Logansicht beenden und `./Test-Stream.ps1` ausführen. Keine Volumes löschen. Keine Zugangsdaten teilen. Der Fix wurde statisch geprüft, nicht auf einer GPU ausgeführt.

Referenz: https://github.com/andimarafioti/faster-qwen3-tts/blob/main/README.md

## Jarvis model settings / Modelleinstellungen (1.8.0)

With Jarvis Tablet Audio 1.5.0, the dashboard's **AI models and performance** panel selects installed text and vision models and a matching context (2048/4096/8192 tokens) and residency (0/60/120/300/600 seconds). Selecting `qwen3-vl:4b-instruct` for both avoids alternating model weights; verify real VRAM peaks alongside Whisper and TTS. Ollama still permits one loaded model and one parallel request. No automatic downloads, new service, public Ollama endpoint or volume changes are added. Legacy vision callers retain immediate unload by default.

The authenticated `GET /runtime` reports only allowlisted installed/loaded models. `POST /describe` additionally accepts bounded `keep_alive` and `num_ctx` and reports inference timing metrics. The HA integration supplies saved parameters; its existing Ollama conversation agent receives matching settings through native config-subentry persistence, preserving prompts, tools and history. Browser clients never receive the worker key. Camera-display commands still bypass both inference models. Settings changes apply on the next request; the first request after idle/restart may load the model.

DE: Unter **Jarvis → Assistent und Audio → KI-Modelle und Leistung** Text-/Bildmodell, Warmhaltezeit und Kontext wählen. Für gemeinsamen Betrieb beide Modelle auf Qwen3-VL 4B Instruct setzen und speichern. Zurückwechseln: Textmodell Qwen3 4B Instruct, Bildmodell Qwen3-VL 4B Instruct. Die Einstellungen gelten zentral für alle Jarvis-Geräte. Höhere Kontextwerte benötigen mehr GPU-Speicher. Vorhandene `.env`, Modelle und Volumes behalten; beim Update nur den Dienst `vision` neu bauen/starten. Kein APK-Update erforderlich.
