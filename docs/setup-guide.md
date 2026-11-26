# TAFA einrichten – Schritt für Schritt

[English](en/setup-guide.md) · [Projektübersicht](../README.de.md) · [App-Anleitung](app.md)

Dieser Leitfaden beschreibt **Neuinstallationen**. Die TAFA-App enthält das Control Center und kann CPU-Sprachdienste selbst bereitstellen. Ein Proxmox-Sprachserver, GPU-Worker, Ollama und öffentliche Alexa-MP3-Durchsagen sind **optional**. Alte Jarvis-Integrationen und Tokens aus früheren Versionen gehören nicht zur Neuinstallation; siehe [Migration und Altinstallation](home-assistant.md).

## 1. TAFA in Home Assistant installieren

Voraussetzungen: Home Assistant OS mit **Apps**, Version ab **2026.11**, auf `amd64` oder `aarch64`; ein Android-Gerät (Android 9+) für die Device Bridge. Vorhandene Home-Assistant-Konfiguration sichern.

1. Unter **Einstellungen → Apps → App installieren → Repositories** das Repository `https://github.com/michaelbudisch/tablet-assist-for-alexa` hinzufügen, die App **TAFA** installieren und starten.
2. **Apps → TAFA → Benutzeroberfläche** öffnen. Eine neue Installation startet mit `speech_mode=setup`: CPU-Modelle werden zunächst **nicht** heruntergeladen. Den Sprachmodus bei **Einstellungen** bewusst auswählen (lokal oder extern).
3. Die App legt eine gemeinsame HA-Integration `tablet_assist_for_alexa` bereit. **Home Assistant Core einmal neu starten**, wenn die Integration erstmals installiert oder aktualisiert wurde; danach gegebenenfalls die TAFA-App neu starten. Nicht zusätzlich die Marketplace-Version installieren.
4. Unter **Einstellungen → Geräte & Dienste** sicherstellen, dass **TAFA** eingerichtet ist. Unter **Einstellungen → Sprachassistenten** die Pipeline **TAFA Lokal** kontrollieren; falls sie nicht automatisch erstellt wurde, mit den TAFA-Routern anlegen: **Tablet Assist Sprachrouter** (STT), **Tablet Assist Gesprächsrouter** (Gespräch), **Tablet Assist Stream** (TTS). Vorhandene andere Pipelines bleiben bestehen.

Die tägliche Bedienung erfolgt über **Übersicht**, **Verbindungen**, **Einstellungen**, **Geräte & Multiroom**, **Wartung & Hilfe** und den separaten Menüpunkt **Jetzt sprechen**. In **Verbindungen** stehen IPs, URLs, CPU-/GPU-Wyoming-Entitäten, Ollama-Agent und der JSON-Import. **Einstellungen** enthält Sprachmodus, Stimmen und Verhalten, nicht die Serveradressen.

## 2. CPU-Spracherkennung und CPU-Stimme einrichten

Es gibt zwei alternative Betriebsarten:

| Betriebsart | Was wird benötigt? | Einrichtung |
| --- | --- | --- |
| **TAFA lokal** | Ausreichend RAM und Speicherplatz für Piper und Faster-Whisper im TAFA-App-Container | **Einstellungen → Sprachmodus: Lokal** wählen, speichern und TAFA neu starten. Ersten Modell-Download und Bereitschaft abwarten. |
| **Externer CPU-Sprachserver** | Ein separater Debian-/Proxmox-Sprachserver mit Piper HTTP und Wyoming-Whisper | Zuerst [CPU-Sprachserver installieren](proxmox.md), dann **Sprachmodus: Extern** und unter **Verbindungen** `http://CPU-SERVER:5000` als Piper-Adresse eintragen. |

**Bei externem CPU-Whisper zusätzlich:** Unter **HA → Einstellungen → Geräte & Dienste → Integration hinzufügen → Wyoming Protocol** den CPU-Host mit Port **10300** hinzufügen. Anschließend unter **TAFA → Verbindungen → CPU-Fallback** die **tatsächlich in HA angelegte** `stt.*`-Entität auswählen. Der Piper-Port 5000 ist **kein STT-Port**. Bei mehreren Wyoming-Instanzen CPU und GPU nicht vertauschen.

Bei lokalem TAFA-Modus werden die eingebauten CPU-Dienste verwendet; ein zweiter Proxmox-Server ist dafür nicht erforderlich. Die CPU-Rückfallebene betrifft **Whisper/STT und Piper/TTS**. Sie stellt ohne separaten Konversationsagenten **kein CPU-Ollama-LLM** bereit.

## 3. GPU-Worker und freie KI optional ergänzen

Auf einem Windows-PC mit passender NVIDIA-GPU, Docker Desktop/WSL2, oder Linux mit Docker/NVIDIA Toolkit den [GPU Worker](worker.md) einrichten. Windows im Verzeichnis `worker/`:

1. `01-Installieren.bat` ausführen; bei Bedarf vorher `00-Konfiguration.bat`. Whisper und Qwen werden eingerichtet; Ollama ist optional und benötigt ein installiertes Textmodell.
2. `04-Verbindungsdaten.bat` ausführen. Das Skript erzeugt **`tafa-worker.json`** und **`GPU-Worker-Verbindungsdaten.txt`**.
3. In **TAFA → Verbindungen → Schnelleinrichtung per JSON** die JSON-Datei auswählen, **Konfiguration prüfen** und die vorgeschlagenen GPU-Adressen übernehmen. Die TXT erklärt die Ports. CPU-Serveradressen stehen **nicht** in diesem GPU-Export und werden separat konfiguriert.
4. Für GPU-Whisper unter **HA → Geräte & Dienste → Wyoming Protocol** die GPU-IP, Port **10300**, hinzufügen und die daraus entstehende GPU-`stt.*`-Entität unter **TAFA → Verbindungen → GPU/KI** auswählen. Die GPU-IP für die schnelle Erreichbarkeitsprüfung ist die **reine IP ohne Port**. Nur eine Qwen-URL einzutragen aktiviert **kein** GPU-Whisper.
5. Optional **Ollama** als HA-Integration mit `http://GPU-IP:11434` hinzufügen, den Konversationsagenten einrichten und seine echte `conversation.*`-Entität in **TAFA → Verbindungen** auswählen. **Ollama für Text/KI ist ein eigener Dienst**, nicht Qwen-TTS.

Für die Sprachausgabe wird Qwen über `http://GPU-IP:10502` bevorzugt; **Tablet Assist Stream** schaltet bei Nichterreichbarkeit vor Wiedergabebeginn auf Piper zurück. Der **Tablet Assist Sprachrouter** kann von GPU-Wyoming auf eingerichtetes CPU-STT zurückfallen. Bei einem Ausfall des GPU-PCs sind freie LLM-Antworten ohne eigenen zusätzlichen CPU-Konversationsagenten möglicherweise nicht verfügbar.

## 4. Android-Gerät mit Home Assistant verbinden

1. Die aktuelle signierte [TAFA Device Bridge](../android/README.de.md) installieren. Pro Tablet in HA einen **eigenen aktiven Benutzer ohne Administratorrechte** anlegen und dessen Zugangsdaten beziehungsweise Zugriffstoken nur auf diesem Gerät verwenden.
2. In der Device Bridge unter **Verbinden** die HA-Basisadresse (ohne Dashboard-Pfad) und den Zugriff einrichten. Mikrofonberechtigung ausdrücklich erteilen.
3. Bei Bedarf den Echo **in Android über Bluetooth als Medienlautsprecher** koppeln und unter **Einstellungen → Echo & Audioplayer** den Player starten. Das **Echo-Mikrofon** nimmt die TAFA-Frage nicht entgegen.
4. Unter **Einstellungen → Rufwort** das lokale Modell einrichten, Rufwort auswählen und den Dienst starten. Im nativen Mikrofonmodus stehen **Stumm**, **Rufwort** und optional **Immer an** zur Wahl; „Immer an“ kann auch auf Hintergrundgespräche reagieren.
5. Unter **TAFA → Geräte & Multiroom** das registrierte Tablet einem Raum und dessen HA-Benutzer zuordnen. [Multiroom-Anleitung](../homeassistant/examples/MULTIROOM.de.md).

## 5. Eine vollständige Anfrage prüfen

1. Unter **TAFA → Verbindungen** die tatsächlich benötigten CPU-/GPU-Dienste kontrollieren. Ein erreichbarer Port beweist noch keine erfolgreiche Spracherkennung.
2. Unter **HA → Einstellungen → Sprachassistenten → TAFA Lokal** die drei TAFA-Router prüfen.
3. Unter **TAFA → Jetzt sprechen** Mikrofonzugriff **über HTTPS oder localhost** erteilen, eine Frage stellen und STT-, Gesprächs- und TTS-Zeiten ansehen. Das ist ein **Browser-Diagnosetest**, dessen Wiedergabe im Browser läuft, **kein Echo-/Tablet-Ausgabetest**.
4. Auf dem Tablet **Jetzt sprechen** und danach das eingestellte Rufwort testen. Für echte Echo-Ausgabe müssen der Android-Player aktiv und der Echo per Bluetooth verbunden sein.
5. Mit eingeschaltetem GPU-PC eine Frage testen, dann den GPU-Worker gezielt stoppen und Whisper-/Piper-CPU-Fallback prüfen. Für GPU-/CPU-STT die Router-Attribute zum tatsächlich verwendeten Backend kontrollieren.

Fehlt ein `stt.*`- oder `conversation.*`-Eintrag, diesen zunächst **in Home Assistant** über die betreffende Integration erzeugen; das reine Eintragen einer IP in TAFA erzeugt keine Wyoming- oder Ollama-Entität.

## 6. Zusätzliche Funktionen

- **Mehrere Tablets:** [Geräte & Multiroom](../homeassistant/examples/MULTIROOM.de.md) – Benutzer und Räume getrennt verwalten.
- **Kamera/Vision:** [Kameraberechtigungen und Einrichtung](../android/docs/camera-preparation.de.md); Kamera ist standardmäßig deaktiviert.
- **Alexa-MP3-Durchsagen:** [Proxmox/HTTPS](proxmox.md) und [Nginx](nginx-proxy.md). **Nur** hierfür benötigt Alexa öffentlich erreichbare, gültige HTTPS-Audiodateien. Normale Bluetooth-Antworten benötigen keine öffentliche Domain.
- **Alternative ohne TAFA-App:** [Marketplace-Installation](marketplace.md), nicht gleichzeitig mit der App-verwalteten Integration.
- **Sicherheit:** [Hinweise](security.md). Keine CPU-/GPU-Modellports öffentlich freigeben; normale HA-Zugriffstokens bleiben erforderlich, auch wenn Worker-LAN-APIs keine zusätzlichen TAFA-API-Tokens verwenden.

**Versionshinweis:** Funktionen und UI dieser Anleitung beziehen sich auf die TAFA-App, die im Repository ausgeliefert wird. Den installierten Stand in der App, die HA-Integration und die signierte Device Bridge getrennt prüfen. Ein vollständiger physischer Erstinstallationstest auf jeder unterstützten Hardware ist dadurch nicht ersetzt.
