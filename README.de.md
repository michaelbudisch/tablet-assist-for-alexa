# TAFA — Tablet Assistant for Alexa

**Eine Home-Assistant-App für das komplette lokale Sprachassistenten-Backend.** TAFA über Home Assistant Apps installieren und die bereits vorhandene **TAFA Device Bridge 1.0.5** auf dem Android-Gerät weiterverwenden. Die native Tablet-App wird separat als signierte APK bereitgestellt.

[English](README.md) | **Deutsch**

> **Ab App 0.3.24:** Neue Installationen starten im **Einrichtungsmodus ohne automatische Sprachmodell-Downloads**. Zuerst GPU-Worker oder Proxmox-Sprachserver installieren, JSON exportieren, dann unter **TAFA Control Center → Einrichtung** importieren, prüfen und bestätigen. TAFA übernimmt Verbindungen und erstellt den Sprachassistenten „TAFA Lokal“, sobald die Komponenten bereitstehen. Neu installierte HA-Integrationen können einen ausdrücklich erlaubten einmaligen HA-Core-Neustart benötigen; der bestätigte Import wird danach fortgesetzt.


[![TAFA-App-Repository hinzufügen](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa)

> **Release-Kandidat / Entwicklungsvorschau:** TAFA Home-Assistant-App **0.3.27**, HA-Integration **0.4.13**, Device Bridge **1.0.1**. Automatisierte Prüfungen für Integration, Container-Build und Schnittstellen sind eingerichtet. Eine vollständige HA-OS-Neuinstallation und ein praktischer Audio-/Tablet-Test fehlen noch vor einem stabilen Release.

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
6. Die [TAFA Device Bridge 1.0.5](android/README.de.md) für Rufwort-Ereignisse und Audio mit HA verbinden. Die Pipeline **TAFA Lokal** in Home Assistant Assist oder der HA Companion App auswählen – nicht in der Device Bridge. Der Echo dient optional als Bluetooth-Lautsprecher, nicht als Mikrofon.

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

**Neu: Sprachtest ohne YAML.** Unter **TAFA → Geräte → Sprachtest** lässt sich eine Frage über das Browser-Mikrofon stellen und die Qwen/Piper-Antwort auf dem verbundenen Tablet hören. Benötigt HTTPS und die vollständige TAFA Lokal-Pipeline. Die Android-App bleibt unverändert. [Anleitung](docs/setup-guide.md).

**Neu in App 0.3.15 / Integration 0.4.7:** Unter **TAFA → Geräte → Sprachtest** kannst du die Sprachausgabe auf dem verbundenen Tablet auch ohne HTTPS testen. Der separate Mikrofontest benötigt weiterhin HTTPS. [Anleitung](docs/setup-guide.md).

**Neu in TAFA 0.3.16 / Integration 0.4.8:** Bei externen Proxmox-Sprachservern prüft TAFA die Wyoming-STT-Anbindung und die vollständige Assist-Pipeline, bevor die Einrichtung als bereit gilt. Eine einzelne Wyoming-STT-Entität wird automatisch gewählt, bei mehreren `cpu_stt` konfigurieren. Die optionale native Android-1.0.1-Sprachaufnahme wird unter **TAFA → Geräte** erklärt. [Einrichtung](docs/setup-guide.md).

**Neu:** Im **TAFA Control Center** lassen sich CPU- und GPU-Whisper über Dropdowns aus bereits eingebundenen Wyoming-Entitäten auswählen. Der **GPU-Worker 2.2.2** schreibt eine vollständige DE/EN-Verbindungs- und Einrichtungsliste (`04-Verbindungsdaten.bat`), inklusive Ollama-Integration für freie KI-Fragen. [Anleitung](docs/setup-guide.md).

**TAFA App 0.3.19 Hotfix:** Fehlende Wyoming-Picker-Datei im Docker-Image ergänzt. App aktualisieren bzw. neu erstellen; bestehende Einstellungen und Android-App bleiben unverändert.

**TAFA 0.3.21 / GPU-Worker 2.2.3:** Die TAFA-Benutzeroberfläche prüft konfigurierte private Sprach-Endpunkte (Piper, Qwen, GPU-Wyoming-TCP, MP3) und zeigt den zuletzt verwendeten Spracherkennungsrechner, sofern Home Assistant diesen meldet. Die automatisch erzeugte Worker-TXT ist auf die drei relevanten GPU-Endpunkte und ihre Eintragungsorte gekürzt. Proxmox-IP-Adressen bleiben manuell zu übernehmen.

**TAFA App 0.3.22:** Das Control Center nutzt vier übersichtliche Tabs (Übersicht, Einrichtung, Verbindungen, Wartung & Hilfe) sowie eine ruhigere Navy-/Petrol-Farbpalette mit Hell-/Dunkelmodus. Status und Verbindungen sind kompakter; vorhandene Einstellungen und Endpunkte bleiben unverändert.

**TAFA 0.3.26 (Kompatibilitätskorrektur):** Falls Home Assistant trotz Aktualisierung noch die ältere Integration im Speicher hat und beim erneuten Wyoming-JSON-Import `Previously mapped integration missing; review first` meldet, versucht TAFA den bestätigten Import einmal mit bereinigten alten Zuordnungen. Nur diese spezielle Fehlermeldung löst eine Wiederholung aus; andere Fehler bleiben sichtbar. Auf Dauer die HA-Integration 0.4.12 laden (Home Assistant Core neu starten). Keine Änderungen am Worker nötig.

**TAFA 0.3.27 / Integration 0.4.13:** Beim JSON-Import prüft TAFA die getrennten Rollen für CPU- und GPU-Wyoming. Falls das importierte GPU-Whisper bereits im alten CPU-Feld steht, wird nur diese veraltete Gegenzuordnung bereinigt. Eine tatsächlich andere CPU-STT-Entität bleibt erhalten. Gleiches gilt umgekehrt für den Import des Proxmox-Sprachservers. Der HA-Abgleich setzt eine GPU-Entität nicht mehr automatisch als CPU ein. Für einen echten externen CPU-Fallback den Proxmox-JSON-Import nutzen. Nach Update der HA-Integration Home Assistant Core einmal neu starten.

**TAFA 0.3.28:** Das zuletzt verbliebene Problem `CPU and GPU Wyoming entities must differ` wird beim bestätigten JSON-Import jetzt unmittelbar vor dem Supervisor-Speichern geprüft und behoben, auch wenn sich Einstellungen zwischen Import und Speicherung verändert haben. Der jeweils andere STT-Wert wird nur dann geleert, wenn er exakt dieselbe Entität wie der importierte Server referenziert. Eine separate CPU-/GPU-Entität bleibt erhalten. Die manuelle Einstellungsprüfung bleibt streng; das automatische Bereinigen gilt nur für einen ausdrücklich bestätigten JSON-Import.

## TAFA Dashboard (ab 0.3.29 / Integration 0.4.14)

Die bisherige TAFA Sprachzentrale wird durch **TAFA Dashboard** als Startpanel der Home-Assistant-Integration ersetzt. Das Dashboard enthält die Bereiche Start, Licht, Energie/Solar, Speicher, Wallbox, Heizung, Wärmepumpe, Heizöl, Geräte, Kameras, Wetter, Abfall, Einkauf und Assist. Über **Dashboard einrichten** können Administratoren die Abschnitte aktivieren und passende HA-Entitäten auswählen; diese Zuordnungen werden zentral in Home Assistant gespeichert und sind auf allen Tablets gleich. Die alte Sprachzentrale ist als **Sprachdienste** weiterhin erreichbar. Es werden keine eigenen Automatisierungen erzeugt oder verändert.

Das öffentliche Dashboard nutzt bewusst keine privaten Sensor-IDs oder altspezifischen Jarvis-Skripte. Auf einem neuen HA können die Module ohne vorkonfigurierte Geräte zunächst leer erscheinen; Gerätedaten werden erst nach der Auswahl angezeigt. Die separate eigene Kiosk-Karte bleibt auf der bestehenden Installation erhalten.

**TAFA 0.3.30 / Integration 0.4.15:** Wenn der externe Piper-Sprachserver während der Erstinstallation noch nicht erreichbar ist, kann in der TAFA-HA-Integration ausdrücklich `dashboard_only` gewählt werden. Die Oberfläche einschließlich zentraler Gerätezuordnungen läuft dann bereits; die Spracherkennung und -ausgabe werden später über den Proxmox- bzw. GPU-JSON-Import angeschlossen. Der gewöhnliche Sprachmodus verlangt weiterhin den Piper-Gesundheitstest.

**TAFA 0.3.31 / Integration 0.4.16:** Das integrierte Dashboard und der Editor verwenden eigene Komponentennamen. Deine bereits installierte Lovelace-Vorschau `tafa-home-dashboard` und das neue TAFA Dashboard können damit gleichzeitig geöffnet werden, ohne sich im Browser gegenseitig zu ersetzen.


**Ab TAFA 0.3.32 / Integration 0.4.17:** Die zusätzliche Leiste über dem Dashboard entfällt. **TAFA** in der unteren Navigation führt direkt zu den Sprachdiensten, das **Zahnrad** in der Dashboard-Kopfzeile öffnet für Administratoren die zentrale Geräte-/Modulkonfiguration. Zurück/Speichern/Abbrechen erscheinen nur in diesen Unteransichten. Die Funktionen und Zuordnungen bleiben erhalten.


**TAFA 0.3.33 / Integration 0.4.18:** Mit **TAFA** in der unteren Dashboard-Navigation öffnen sich Geräteverwaltung, Alexa-Durchsagen, Sprachstatus, Datenquellen und optionale Lernfunktionen direkt **innerhalb der Dashboard-Oberfläche**. Alle Karten, Buttons und Tabs übernehmen die Dashboard-Farben und -Abstände. Für die unabhängige Nutzung gibt es in den Sprachdiensten einen Link zur separaten Ansicht `/tablet_assist_for_alexa?view=voice`, die dieselbe Gestaltung verwendet. Die Einstellungen bleiben im HA-Backend erhalten und Änderungen an Automatisierungen sind nicht nötig.

**TAFA 0.3.34 / Integration 0.4.19 / Android 1.0.2:** Nur noch direkter Sprachweg: Android-Aufnahme (auch bei ausgeschaltetem Bildschirm) → Assist „TAFA Lokal“ → Tablet → Bluetooth-Ausgabe. Keine zusätzliche Browser-Aufnahme oder input_text-Audiosteuerung. Die Anzahl Anschlussfragen wird pro Tablet unter TAFA Dashboard → TAFA → Geräte (0–100 oder unbegrenzt) verwaltet. Das Mikrofon-Symbol steuert den nativen Android-Wakeword-Dienst via HA, bei Multiroom mit Raumauswahl. Bereits zugeordnete alte Geräte werden beim ersten Start lesend übernommen. Das Android-Update auf 1.0.2 benötigt bei bereits signierter APK denselben Signaturschlüssel wie zuvor.

**TAFA 0.3.35 / Integration 0.4.20:** Während die alte Jarvis-Integration für Kamera und bereits angelegte Automatisierungen weiter betrieben wird, lädt TAFA nur die eigenen STT-/TTS-/Gesprächsrouter und die neuen Mikrofon-/Multiroom-Dienste. So entstehen keine kaputten doppelten Kamera- und Bewegungssensoren. Nach dem Update HA Core neu starten.
