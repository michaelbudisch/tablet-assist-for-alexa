# TAFA — Tablet Assistant for Alexa

**Eine Home-Assistant-App für das komplette lokale Sprachassistenten-Backend.** TAFA über Home Assistant Apps installieren und die bereits vorhandene **TAFA Device Bridge 1.0.0** auf dem Android-Gerät weiterverwenden. Die native Tablet-App wird **nicht verändert**.

[English](README.md) | **Deutsch**

> **Neu in App 0.3.12:** Die TAFA-Einstellungen liegen zentral unter **Einstellungen → Apps → TAFA → Konfiguration**. Nach dem Speichern die App neu starten. Bei einem Update Home Assistant einmal neu starten, damit die Integration 0.4.4 geladen wird, dann die App neu starten. Die HA-eigene Wyoming-Integration wird einmal unter Geräte & Dienste hinzugefügt; die TAFA-Auswahl und alle weiteren Einstellungen erfolgen in der App. Vorhandene Assist-Pipelines werden nicht überschrieben. Für reine Marketplace-Installationen bleibt der HA-Optionsdialog erhalten.


[![TAFA-App-Repository hinzufügen](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa)

> **Release-Kandidat / Entwicklungsvorschau:** TAFA Home-Assistant-App **0.3.13**, zusammengeführte HA-Integration **0.4.5**, Device Bridge **1.0.0 unverändert**. Automatisierte Prüfungen für Integration, Container-Build und Schnittstellen sind eingerichtet. Eine vollständige HA-OS-Neuinstallation und ein praktischer Audio-/Tablet-Test fehlen noch vor einem stabilen Release.

**[Einfacher Einrichtungsleitfaden: TAFA lokal, Proxmox, GPU und Alexa-HTTPS](docs/setup-guide.md)**

## Proxmox: neuer kombinierter Sprachserver + Nginx (ein CT)

Für eine frische Proxmox-Installation gibt es jetzt einen geführten **Ein-Zeilen-Installer**, der nur einen **neuen** unprivilegierten CT erstellt (Piper, Wyoming-Whisper, tokenfreier MP3-Generator und Nginx). Bestehende CTs und VM bleiben unverändert:

```bash
curl -fsSLo /root/tafa-pve-install.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/quick-install.sh && bash /root/tafa-pve-install.sh
```

**Auf dem Proxmox-Host als root** ausführen. Der Assistent fragt nach CT-ID, Speicher, Netzwerk, Ressourcen sowie optional GPU-Worker/Audio-Domain und verlangt die CT-ID als Bestätigung. In der CT-Konsole sind IP-Adressen, Ports und Dienste dauerhaft sichtbar. `tafa-info` zeigt den Status, `tafa-setup` führt durch die spätere Alexa-HTTPS-Aktivierung (nach DNS-/Router-Einrichtung). [Ausführliche Anleitung](docs/proxmox.md).

## Schnellinstallation — Home Assistant OS

1. Eine Home-Assistant-Sicherung anlegen. Zuerst möglichst auf einer Testinstallation prüfen.
2. Einstellungen → Apps → App installieren → Repositories: `https://github.com/michaelbudisch/tablet-assist-for-alexa` hinzufügen.
3. **TAFA** installieren, starten und das integrierte Control Center öffnen (Ingress).
4. TAFA stellt **eine** gemeinsame HA-Integration unter `custom_components/tablet_assist_for_alexa` bereit. Home Assistant einmal neu starten, damit die Integration erkannt wird.
5. **Vor dem ersten Start** in der App-Konfiguration `speech_mode=local` (CPU-Modelle in der App) oder `speech_mode=external` und `external_piper_base=http://PROXMOX-IP:5000` auswählen. Bei `external` werden keine lokalen Sprachmodelle gestartet. Die HA-Integration wird vorbereitet; danach Wyoming-STT (`PROXMOX-IP:10300`) in HA hinzufügen, die passende STT-Entität unter Apps → TAFA → Konfiguration im Feld `cpu_stt` auswählen bzw. automatisch erkennen lassen und eine Assist-Pipeline anlegen. Im lokalen Modus erfolgt die Einrichtung der TAFA-Lokal-Pipeline automatisch.
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

Marketplace installiert dieselbe **zusammengeführte TAFA-Integration 0.4.3**, einschließlich öffentlicher Geräte-/Multiroom-Funktionen. Im Unterschied zur Home-Assistant-App enthält Marketplace jedoch **keine laufenden Piper-/Whisper-Dienste**. Diese müssen dort separat bereitgestellt werden. **Nicht gleichzeitig beide Installationswege verwenden.** [Marketplace-Anleitung](docs/marketplace.md).

## Sicherheit, Updates und Altinstallation

- Keine privaten Hosts, Passwörter, Kamerabilder oder privaten Dashboard-Dateien im Release. Mikrofone und Kameras werden nur nach bewusstem Aktivieren und mit passenden Berechtigungen genutzt.
- TAFA versieht neu installierte Komponenten mit einer Verwaltungskennung und aktualisiert ausschließlich eigene, unveränderte Installationen. HACS-, manuelle und veränderte Dateien bleiben unangetastet. Vorherige Versionen landen unter `.tafa/rollback` im HA-Konfigurationsverzeichnis.
- Wenn die alte Integration `jarvis_tablet_audio` noch eingerichtet ist, vermeidet die neue Integration doppelte Relay-Schnittstellen. Eine automatische Altanlagenmigration erfolgt **nicht**.
- Die TAFA-App und der Marketplace sind getrennte Installationswege. Die Android-App bleibt ein unabhängiger Client.

## Anleitungen

[App-Installation DE](docs/app.md) · [App-Installation EN](docs/en/app.md) · [Marketplace](docs/marketplace.md) · [Backend](docs/backend-roadmap.md) · [Datenschutz](docs/security.md) · [GPU-Worker](docs/worker.md) · [Versionshistorie](CHANGELOG.de.md).

## Lizenz

Eigener Projektcode: [MIT](LICENSE). Drittanbieterbibliotheken und heruntergeladene Sprach-/STT-Modelle unterliegen ihren jeweiligen Lizenzen (einschließlich Piper). Unabhängiges Community-Projekt ohne Verbindung zu Amazon oder Home Assistant.

**Tablet-Multiroom (neu):** Unter **TAFA → Geräte** kann ein Administrator jetzt den registrierten Tablet-Geräten einen bestehenden, nicht-administrativen HA-Benutzer und Audio-Raum zuordnen und den Verbindungsstatus sehen. Keine YAML-Aktionen erforderlich; die bestehende Android-App 1.0.0 bleibt unverändert. [Schrittfolge](docs/setup-guide.md).
