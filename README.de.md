# TAFA — Tablet Assistant for Alexa

**Eine Home-Assistant-App für das komplette lokale Sprachassistenten-Backend.** TAFA über Home Assistant Apps installieren und die bereits vorhandene **TAFA Device Bridge 1.0.0** auf dem Android-Gerät weiterverwenden. Die native Tablet-App wird **nicht verändert**.

[English](README.md) | **Deutsch**

[![TAFA-App-Repository hinzufügen](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa)

> **Release-Kandidat / Entwicklungsvorschau:** TAFA Home-Assistant-App **0.3.6**, zusammengeführte HA-Integration **0.4.1**, Device Bridge **1.0.0 unverändert**. Automatisierte Prüfungen für Integration, Container-Build und Schnittstellen sind eingerichtet. Eine vollständige HA-OS-Neuinstallation und ein praktischer Audio-/Tablet-Test fehlen noch vor einem stabilen Release.

## Schnellinstallation — Home Assistant OS

1. Eine Home-Assistant-Sicherung anlegen. Zuerst möglichst auf einer Testinstallation prüfen.
2. Einstellungen → Apps → App installieren → Repositories: `https://github.com/michaelbudisch/tablet-assist-for-alexa` hinzufügen.
3. **TAFA** installieren, starten und das integrierte Control Center öffnen (Ingress).
4. TAFA stellt **eine** gemeinsame HA-Integration unter `custom_components/tablet_assist_for_alexa` bereit. Home Assistant einmal neu starten, damit die Integration erkannt wird.
5. TAFA lädt eine deutsche Piper-Stimme und ein Faster-Whisper-CPU-Modell herunter und zeigt den tatsächlichen Status an. Sobald Sprachserver und HA bereit sind, versucht TAFA automatisch, die Integration einzurichten und eine separate Assist-Pipeline **TAFA Lokal** anzulegen, ohne bestehende Pipelines zu überschreiben.
6. Die unveränderte [TAFA Device Bridge 1.0.0](android/README.de.md) für Rufwort-Ereignisse und Audio mit HA verbinden. Die Pipeline **TAFA Lokal** in Home Assistant Assist oder der HA Companion App auswählen – nicht in der Device Bridge. Der Echo dient optional als Bluetooth-Lautsprecher, nicht als Mikrofon.

[Vollständige Anleitung](docs/app.md) · [Multiroom](homeassistant/examples/MULTIROOM.de.md) · [Android-Einrichtung](android/README.de.md)

## Was die einzige App enthält

| Bestandteil | Funktion |
|---|---|
| TAFA Control Center | Ingress-Oberfläche, echte Statusanzeigen und Einrichtungsführung |
| Eine HA-Integration | STT/TTS/Gesprächsrouter, lokale HA-Befehle, optionale Durchsagen |
| Native Kompatibilität | Authentifizierte `/api/jarvis_tablet_audio/wake_devices`-Schnittstelle und bisherige Wake-Ereignisse |
| Multiroom | Getrennte Geräte, Raum-Audio, optionale freigegebene Kameras und Bewegungsdaten |
| Vision-Schnittstellen | Optionaler externer GPU-Worker; keine automatische Kameraaktivierung |
| Lokale CPU-Sprache | Deutsche Piper-Sprachausgabe und Faster-Whisper-Spracherkennung im TAFA-App-Container |
| Automatische Einrichtung | HA-Konfigurationsdialog und eigene TAFA-Lokal-Pipeline ohne Änderung bestehender Pipelines |
| Sichere Updates | Nur unveränderte, von TAFA installierte Dateien werden aktualisiert; vorherige Versionen werden gesichert |

GPU-Worker, Ollama und Alexa-MP3-Durchsagen sind **optional**. Das private Dashboard ist nicht enthalten. Die CPU-Sprachmodelle werden beim ersten Start heruntergeladen und im persistenten App-Datenverzeichnis gespeichert. Dafür wird einmalig Internet benötigt.

## Native Rufwortübergabe – wichtige Einschränkung

Device Bridge 1.0.0 **sendet ausschließlich das erkannte Rufwort** und gibt danach das Mikrofon frei. Die anschließende Frage wird **nicht** von der Bridge an Home Assistant übertragen. Dafür muss ein eigener, aktiver Assist-Client mit Mikrofonfreigabe übernehmen (zum Beispiel die Home-Assistant-Sprachoberfläche). Das Backend kann nicht auf Sprachdaten zugreifen, die die unveränderte Android-App nicht überträgt. Assist lässt sich unabhängig vom Rufwort manuell starten. Ein vollständig freihändiger Betrieb mit **nur** TAFA-App und Device Bridge 1.0.0 ist daher **noch nicht möglich**. Für einen stabilen All-in-one-Sprachrelease ist das ein offener Punkt.

## Alternative: Home Assistant Marketplace

[![Marketplace-Integration](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration)

Marketplace installiert dieselbe **zusammengeführte TAFA-Integration 0.4.1**, einschließlich öffentlicher Geräte-/Multiroom-Funktionen. Im Unterschied zur Home-Assistant-App enthält Marketplace jedoch **keine laufenden Piper-/Whisper-Dienste**. Diese müssen dort separat bereitgestellt werden. **Nicht gleichzeitig beide Installationswege verwenden.** [Marketplace-Anleitung](docs/marketplace.md).

## Sicherheit, Updates und Altinstallation

- Keine privaten Hosts, Passwörter, Tokens, Kamerabilder oder privaten Dashboard-Dateien im Release. Mikrofone und Kameras werden nur nach bewusstem Aktivieren und mit passenden Berechtigungen genutzt.
- TAFA versieht neu installierte Komponenten mit einer Verwaltungskennung und aktualisiert ausschließlich eigene, unveränderte Installationen. HACS-, manuelle und veränderte Dateien bleiben unangetastet. Vorherige Versionen landen unter `.tafa/rollback` im HA-Konfigurationsverzeichnis.
- Wenn die alte Integration `jarvis_tablet_audio` noch eingerichtet ist, vermeidet die neue Integration doppelte Relay-Schnittstellen. Eine automatische Altanlagenmigration erfolgt **nicht**.
- Die TAFA-App und der Marketplace sind getrennte Installationswege. Die Android-App bleibt ein unabhängiger Client.

## Anleitungen

[App-Installation DE](docs/app.md) · [App-Installation EN](docs/en/app.md) · [Marketplace](docs/marketplace.md) · [Backend](docs/backend-roadmap.md) · [Datenschutz](docs/security.md) · [GPU-Worker](docs/worker.md) · [Versionshistorie](CHANGELOG.de.md).

## Lizenz

Eigener Projektcode: [MIT](LICENSE). Drittanbieterbibliotheken und heruntergeladene Sprach-/STT-Modelle unterliegen ihren jeweiligen Lizenzen (einschließlich Piper). Unabhängiges Community-Projekt ohne Verbindung zu Amazon oder Home Assistant.
