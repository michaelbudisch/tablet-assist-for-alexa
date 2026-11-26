![TAFA — Lokaler KI-Sprachassistent für Home Assistant](docs/assets/tafa-readme-banner.webp)

<p align="center">
  <img src="tafa_app/brand.svg" alt="TAFA" width="88">
</p>

<h1 align="center">TAFA — Tablet Assist for Alexa</h1>

<p align="center"><strong>Lokaler Sprachassistent für Home Assistant – mit Android-Tablet als Mikrofon und Echo als Bluetooth-Lautsprecher.</strong></p>

<p align="center"><a href="README.md">English</a> · <strong>Deutsch</strong></p>

TAFA verbindet die native Spracheingabe auf Android, Home Assistant, lokale Spracherkennung, optionale KI-Modelle und Sprachausgabe. Im Alltag muss dafür weder das Home-Assistant-Dashboard noch die Companion-App geöffnet sein. Die **TAFA Device Bridge** erkennt das Rufwort und nimmt die Frage im Hintergrund auf. Home Assistant verarbeitet sie und sendet die gesprochene Antwort zurück an das Tablet.

## Was kann TAFA?

| Bereich | Funktionen |
| --- | --- |
| **Sprachunterhaltung** | Lokale Rufworterkennung auf Android, Sprachübertragung an Home Assistant Assist, Whisper-Spracherkennung, Gesprächsverarbeitung und gesprochene Antworten. Optionale Anschlussfragen. |
| **Lokale KI** | Home-Assistant-Befehle über HA-Intents und optional Ollama für freie Fragen und Antworten. |
| **Sprachausgabe** | Piper als CPU-Variante, optional Qwen-Stimme über den GPU-Rechner. Die Antwort spielt der native Android-Player ab – auch über einen Bluetooth-gekoppelten Echo. |
| **GPU und CPU** | Spracherkennung auf einem separaten GPU-Worker, sofern verfügbar, mit separat eingerichteter CPU-Rückfallebene. |
| **Multiroom** | Mehrere Tablets registrieren, Räumen zuordnen sowie Mikrofon- und Playerstatus in Home Assistant verwalten. |
| **TAFA Dashboard** | Integriertes HA-Dashboard mit wählbaren Modulen für Licht, Wetter, Energie, E-Auto, Heizung, Haushaltsgeräte, Kameras und mehr. Die Daten stammen aus den vorhandenen HA-Entitäten. |
| **Kameras und Vision** | Optionale Android-Kameraanbindung und lokale Bildauswertung; separat aktivierbar und einzurichten. |
| **Ankündigungen** | Optionale proaktive MP3-Durchsagen über Alexa-Benachrichtigungsdienste. **Nicht** derselbe Weg wie die normale Bluetooth-Sprachausgabe. |

TAFA **ersetzt Alexa nicht**. Ein gekoppelter Echo lässt sich weiterhin normal verwenden. Für TAFA-Gespräche dient er als Bluetooth-Lautsprecher des Tablets; Alexa-Ankündigungen sind unabhängig davon.

## So funktioniert TAFA

**Der normale Sprachweg**

```text
„Hey Jarvis“ → TAFA Device Bridge (Android)
             → Home Assistant Assist / TAFA Lokal
             → Whisper STT (GPU oder CPU)
             → HA-Befehl oder optional lokales Ollama-Modell
             → Qwen / Piper TTS
             → TAFA-Android-Audioplayer → Bluetooth → Echo
```

Die Rufworterkennung erfolgt **lokal auf dem Tablet** und nicht durch wiederholte Whisper-Abfragen. Die Android-App läuft unabhängig vom geöffneten Dashboard weiter. Der separate Button **„Einmal sprechen“** im Control Center bleibt ein Browser-Diagnosetest, keine zweite dauerhaft laufende Rufworterkennung.

**Optionale Ankündigungen:** HA-Automation → generierte MP3 → HTTPS-/Benachrichtigungsintegration → Alexa. Dieser Weg ist bewusst vom Bluetooth-Streaming für Gespräche getrennt.

## Die Bausteine des Projekts

| Baustein | Aufgabe |
| --- | --- |
| **TAFA Home-Assistant-App** | Control Center, Einrichtung, Dienstverbindungen und optionale integrierte CPU-Sprachdienste |
| **TAFA-Integration** | Assist-Routing für STT/TTS/Gespräche, Tablets, Multiroom, Dashboard und optionale Sprach-/Vision-Schnittstellen |
| **TAFA Device Bridge** | Nativer Android-Hintergrunddienst für Mikrofon, Rufwort, Assist-WebSocket und Bluetooth-Audio |
| **Proxmox-Sprachserver** | Optional ausgelagerte CPU-Dienste für Whisper/Piper, MP3-Erzeugung und Proxy |
| **GPU Worker** | Optional GPU-Whisper, Ollama, Qwen-Streaming-TTS und Vision |

Du kannst mit einer CPU-Lösung anfangen und den GPU-Worker später ergänzen. Die verwendeten Dienste werden im TAFA Control Center zugeordnet; zusätzliche Hardware, Modelle und Home-Assistant-Integrationen werden nicht vorausgesetzt.

## TAFA installieren

**Schnellstart für neue Nutzer:** TAFA als Home-Assistant-App installieren → im Control Center zwischen **Lokal** und **Extern** für CPU-Sprachdienste wählen → Home Assistant Core nach Installation der Integration einmal neu starten → aktuelle **TAFA Device Bridge** auf Android verbinden → **TAFA Lokal** und Bluetooth-Ausgabe mit einer echten Frage testen. **Ein neuer TAFA-Start befindet sich zunächst im Einrichtungsmodus und lädt keine CPU-Modelle automatisch.** Der GPU Worker ist optional; seine JSON-Verbindungsdaten werden unter **TAFA → Verbindungen** importiert.

Der **[Schritt-für-Schritt-Einrichtungsleitfaden](docs/setup-guide.md)** beschreibt die verschiedenen Installationswege und die Verbindung der Komponenten. Befehle, IP-Adressen und Netzwerkkonfiguration stehen in den jeweiligen Anleitungen – nicht mehr im Mittelpunkt dieser Projektvorstellung.

[![TAFA-App-Repository hinzufügen](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa)

- [Home-Assistant-App installieren](docs/app.md) · [Native Android-App und kompatible APKs](android/README.de.md)
- [CPU-Sprachserver auf Proxmox](docs/proxmox.md) · [Optionaler GPU-Worker](docs/worker.md)
- [Multiroom einrichten](homeassistant/examples/MULTIROOM.de.md) · [Optionale HA-Automationen](docs/ha-automations.md)
- [Marketplace-Integration](docs/marketplace.md) – **Alternative** zur App-verwalteten Integration, keine zusätzliche zweite Installation
- [Sicherheit](docs/security.md) · [Versionshistorie](CHANGELOG.de.md)

### Entwicklungsstand

TAFA wird aktiv weiterentwickelt. Das integrierte Dashboard und der native Sprachweg sind im Projekt enthalten; eine frische Installation und die Audioausgabe sollten auf der jeweiligen Hardware geprüft werden. **Der Android-Quellcode kann neuer sein als die zuletzt veröffentlichte signierte APK.** Für ein Update über die vorhandene Device Bridge muss die APK mit *demselben Zertifikat* signiert sein. Eine Debug-APK aus GitHub Actions ist kein Ersatz für eine bereits signierte App.

In der signierten Device Bridge 1.2.3 ist der optionale native Modus **„Immer an“** enthalten: Er erkennt Sprachaktivität ohne Rufwort und kann dabei auch durch Hintergrundgespräche ausgelöst werden. Der bewährte Rufwortmodus bleibt die Standardeinstellung. Siehe [Android-Installation](android/README.de.md).

## Datenschutz und Kompatibilität

Die Sprachverarbeitung kann im eigenen Netzwerk bleiben. Die Device Bridge verwendet einen bewusst gestarteten Android-Mikrofon-Vordergrunddienst; Kameras und externe Zugriffe benötigen eine gesonderte Einrichtung und Berechtigungen. Die optionale öffentliche Bereitstellung von Alexa-MP3-Dateien sollte gezielt eingerichtet werden. TAFA enthält keine privaten Dashboards, persönlichen Entitäts-IDs oder Zugangsdaten. Vorhandene HA-Automationen werden nicht automatisch ersetzt oder migriert.

Das Projekt ist unabhängig und steht in keiner Verbindung zu Amazon oder Home Assistant.

**Lizenz:** [MIT](LICENSE) für den eigenen Projektcode. Drittanbieterbibliotheken und heruntergeladene Modelle unterliegen ihren jeweiligen Lizenzen.
