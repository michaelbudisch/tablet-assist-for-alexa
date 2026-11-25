# TAFA als Home-Assistant-App installieren

[English](en/app.md) · [Projektübersicht](../README.de.md)

**TAFA App 0.3.10 — Release-Kandidat, noch nicht auf einem frisch installierten HA OS zertifiziert.** Voraussetzungen: Home Assistant OS ab 2026.11, unterstütztes amd64/aarch64-System sowie ausreichend RAM und Speicher für die deutschen CPU-Sprachmodelle. Die Android Device Bridge 1.0.0 bleibt unverändert.

**Neu:** [Geführte Einrichtung für TAFA lokal, Proxmox, GPU-Worker und Alexa-MP3](setup-guide.md). Alle drei Bereiche sind über **TAFA → Optionen** getrennt erreichbar.

## Installation mit einer App

1. Home-Assistant-Sicherung erstellen. Für die erste Bereitstellung möglichst eine frische Testinstallation nutzen.
2. **Einstellungen → Apps → App installieren → Repositories** öffnen, `https://github.com/michaelbudisch/tablet-assist-for-alexa` hinzufügen und **TAFA** installieren. **Vor dem Start** im App-Reiter **Konfiguration** den Sprachmodus auswählen: `local` oder `external` mit `external_piper_base=http://PROXMOX-IP:5000`.
3. App starten und das **TAFA Control Center** öffnen. Nur bei `local` werden CPU-Sprachmodelle heruntergeladen. Bei `external` bleibt die lokale CPU-Verarbeitung aus; die Proxmox-Piper-Verbindung wird geprüft.
4. TAFA stellt **eine** Integration bereit: `custom_components/tablet_assist_for_alexa`. Home Assistant über die normalen Einstellungen **einmal neu starten**. Keine YAML-Bearbeitung und keine zweite HA-Integration bei einer Neuinstallation nötig.
5. Die App versucht den TAFA-Konfigurationsdialog automatisch abzuschließen. Bei `local` wird anschließend die **TAFA Lokal**-Pipeline eingerichtet. Bei `external` zuerst **Wyoming** für `PROXMOX-IP:10300` hinzufügen, unter **Geräte & Dienste → TAFA → Optionen → Sprachserver & GPU** als CPU-STT auswählen und eine Assist-Pipeline mit **TAFA STT-Router** und **Tablet Assist Stream** anlegen. Vorhandene Pipelines bleiben unverändert; keine `.storage`-Änderungen.
6. Die vorhandene [TAFA Device Bridge 1.0.0](../android/README.de.md) für Rufwort und Audio verbinden. **TAFA Lokal** in Home Assistant Assist beziehungsweise in der HA Companion App wählen, nicht in der Device Bridge. Optional den Echo über Android-Bluetooth als Lautsprecher koppeln. Audio-, Kamera- und Rufwortberechtigungen bleiben unter Android-Kontrolle.

## Einschränkung bei der Rufwortübergabe

Device Bridge 1.0.0 sendet das erkannte Rufwort und gibt anschließend das Mikrofon frei, überträgt aber nicht die Frage. Nach dem Ereignis muss ein aktiver Assist-Client die Frage mit eigener Mikrofonfreigabe aufnehmen; diese fehlenden Audiodaten kann das Backend allein nicht erzeugen. Manuelles Assist funktioniert unabhängig davon. Vollständig freihändige Nutzung mit nur der unveränderten Bridge und TAFA-App darf deshalb noch nicht als unterstützt gelten.

## Automatische Qwen-/Piper-Sprachausgabe

Ab TAFA App 0.3.10 verwendet eine **neu erstellte** Assist-Pipeline `TAFA Lokal` standardmäßig den **Tablet Assist Stream**-TTS-Provider. Solange kein GPU-Worker konfiguriert oder erreichbar ist, erzeugt Piper die Sprache. Ist ein Qwen-Worker ohne zusätzlichen API-Schlüssel über die **TAFA-Integration unter Einstellungen → Geräte & Dienste** eingerichtet und bereit, wird Qwen verwendet. Bei Ausfall fällt der Router wieder auf Piper zurück. Ein GPU-Worker wird nicht automatisch im Netzwerk gesucht; Die Adresse muss bewusst eingerichtet werden.

**Bereits vorhandene TAFA-Lokal-Pipelines werden nicht automatisch geändert.** Wer die bisherige Piper-only-Engine verwendet, stellt in der Assist-Pipeline die Sprachausgabe auf **Tablet Assist Stream** um. Das gilt für die normale Assist-Sprachausgabe; Alexa-MP3-Durchsagen über den HTTPS-Proxy bleiben ein separater Pfad.

## Inhalt der App

- Eine gemeinsame HA-Integration mit STT, TTS, Gesprächsrouter, nativem Wake-Geräteregister, authentifizierter Kompatibilitätsschnittstelle, Multiroom, optionalen Kamera-/Bewegungsdaten und Vision-Diensten.
- **Lokaler Modus:** deutsche CPU-Sprachdienste Piper und Faster-Whisper laufen im App-Container, Modelle bleiben in `/data`. **Externer Modus:** keine lokalen CPU-Prozesse oder Modell-Downloads; Piper und Wyoming-Whisper bleiben auf Proxmox. Keine öffentlich freigegebenen Ports.
- GPU-Worker, Ollama und Alexa-MP3-/HTTPS-Durchsagen sind optional und werden separat eingerichtet.
- Das private TAFA-Dashboard und der Android-APK-Quellcode bleiben unverändert.

## Fehlerbehebung: Update bricht beim Docker-Build ab

Wenn das Supervisor-Protokoll meldet `NumPy was built with baseline optimizations: (X86_V2) but your machine doesn't support (X86_V2)`, wird das durch eine ältere CPU beziehungsweise ein generisches virtuelles CPU-Profil ausgelöst. **App 0.3.9 pinnt NumPy 1.26.4**, das die X86_V2-Baseline von NumPy ab 2.4 nicht voraussetzt. Zuerst das App-Repository aktualisieren und **TAFA 0.3.10** installieren; keine Neuinstallation und keine HA-Integration löschen. Bleibt ein anderer Fehler wie `illegal instruction`, im Virtualisierungshost die CPU-Kompatibilität prüfen; weitere native Bibliotheken haben eigene CPU-Anforderungen.

## Fehlerbehebung: Piper oder Whisper nicht bereit

In der ersten Testinstallation mit App 0.3.4 konnten Piper mit `RuntimeError` und Whisper mit `ImportError` abbrechen. Ab 0.3.9 werden native Sprachbibliotheken beim Docker-Build geladen, eSpeak-Systemdaten installiert und der tatsächliche Fehler (nicht nur die Fehlerklasse) im Control Center angezeigt.

Unter **Einstellungen → Apps → TAFA → Aktualisieren** die neue Version installieren, TAFA neu starten und im Control Center die beiden Modellzustände prüfen. Herunterladen kann beim ersten Start Zeit und Internet benötigen. Bei einem Fehler **Sprachmodelle erneut laden** wählen; bei weiterhin bestehendem Fehler die vollständige Meldung aus dem Control Center beziehungsweise dem TAFA-App-Protokoll prüfen. Die HA-Integration muss hierfür nicht neu installiert werden.

## Updates, Sicherheit und Grenzen

- Die App aktualisiert ausschließlich unveränderte, selbst installierte Integrationsdateien. Vorherige Versionen werden unter `<HA-Konfiguration>/.tafa/rollback` gesichert. Manuelle/HACS-Installationen und veränderte Dateien bleiben unangetastet. Nach Backend-Updates HA neu starten.
- Ist `jarvis_tablet_audio` noch eingerichtet, verhindert TAFA die doppelte Registrierung der alten Native-Endpunkte; die Altinstallation wird **nicht automatisch migriert**. Vorher sichern und getrennt umstellen.
- Mikrofone und Kameras werden nur nach bewusster Aktivierung verwendet. Audio wird im Speicher verarbeitet, die CPU-Schnittstellen haben Größenbegrenzungen. Der erstmalige Modell-Download benötigt Internet.
- Offene Release-Prüfungen: saubere HA-OS-Installation, Modell-Download, Assist/Device Bridge/Bluetooth sowie mehrere echte Tablets gleichzeitig. Siehe [Release-Checkliste](release.md).

[Marketplace ohne App](marketplace.md) · [Multiroom](../homeassistant/examples/MULTIROOM.de.md) · [Optionaler GPU-Worker](worker.md)
