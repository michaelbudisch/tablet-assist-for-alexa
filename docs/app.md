# TAFA als Home-Assistant-App installieren

[English](en/app.md) · [Projektübersicht](../README.de.md)

**TAFA App 0.3.2 — Release-Kandidat, noch nicht auf einem frisch installierten HA OS zertifiziert.** Voraussetzungen: Home Assistant OS ab 2026.11, unterstütztes amd64/aarch64-System sowie ausreichend RAM und Speicher für die deutschen CPU-Sprachmodelle. Die Android Device Bridge 1.0.0 bleibt unverändert.

## Installation mit einer App

1. Home-Assistant-Sicherung erstellen. Für die erste Bereitstellung möglichst eine frische Testinstallation nutzen.
2. **Einstellungen → Apps → App installieren → Repositories** öffnen, `https://github.com/michaelbudisch/tablet-assist-for-alexa` hinzufügen, **TAFA** auswählen, installieren und starten.
3. Das **TAFA Control Center** öffnen. CPU-Sprachmodelle werden beim ersten Start heruntergeladen (Internet nötig). Die Statuskarten zeigen tatsächliche Bereitschaft oder Fehler von Piper und Whisper.
4. TAFA stellt **eine** Integration bereit: `custom_components/tablet_assist_for_alexa`. Home Assistant über die normalen Einstellungen **einmal neu starten**. Keine YAML-Bearbeitung und keine zweite HA-Integration bei einer Neuinstallation nötig.
5. Die App versucht, den HA-Konfigurationsdialog über die Supervisor-Core-API automatisch abzuschließen, und erstellt anschließend eine **TAFA Lokal**-Assist-Pipeline, sobald STT, TTS und Gesprächsrouter registriert sind. Bestehende Pipelines bleiben unverändert. Wenn die automatische Einrichtung fehlschlägt, unter **Einstellungen → Geräte & Dienste → Integration hinzufügen → TAFA** wechseln und die verfügbaren Sprachdienste im Control Center prüfen. Nicht manuell in `.storage` eingreifen.
6. Die vorhandene [TAFA Device Bridge 1.0.0](../android/README.de.md) installieren/verbinden und TAFA Lokal wählen. Optional den Echo über Android-Bluetooth als Lautsprecher koppeln. Audio-, Kamera- und Rufwortberechtigungen bleiben unter Android-Kontrolle.

## Inhalt der App

- Eine gemeinsame HA-Integration mit STT, TTS, Gesprächsrouter, nativem Wake-Geräteregister, authentifizierter Kompatibilitätsschnittstelle, Multiroom, optionalen Kamera-/Bewegungsdaten und Vision-Diensten.
- **Deutsche CPU-Sprachdienste Piper und Faster-Whisper** laufen im App-Container. Heruntergeladene Modelle bleiben im persistenten App-Verzeichnis `/data`. Keine öffentlich freigegebenen Ports.
- GPU-Worker, Ollama und Alexa-MP3-/HTTPS-Durchsagen sind optional und werden separat eingerichtet.
- Das private TAFA-Dashboard und der Android-APK-Quellcode bleiben unverändert.

## Updates, Sicherheit und Grenzen

- Die App aktualisiert ausschließlich unveränderte, selbst installierte Integrationsdateien. Vorherige Versionen werden unter `<HA-Konfiguration>/.tafa/rollback` gesichert. Manuelle/HACS-Installationen und veränderte Dateien bleiben unangetastet. Nach Backend-Updates HA neu starten.
- Ist `jarvis_tablet_audio` noch eingerichtet, verhindert TAFA die doppelte Registrierung der alten Native-Endpunkte; die Altinstallation wird **nicht automatisch migriert**. Vorher sichern und getrennt umstellen.
- Mikrofone und Kameras werden nur nach bewusster Aktivierung verwendet. Audio wird im Speicher verarbeitet, die CPU-Schnittstellen haben Größenbegrenzungen. Der erstmalige Modell-Download benötigt Internet.
- Offene Release-Prüfungen: saubere HA-OS-Installation, Modell-Download, Assist/Device Bridge/Bluetooth sowie mehrere echte Tablets gleichzeitig. Siehe [Release-Checkliste](release.md).

[Marketplace ohne App](marketplace.md) · [Multiroom](../homeassistant/examples/MULTIROOM.de.md) · [Optionaler GPU-Worker](worker.md)
