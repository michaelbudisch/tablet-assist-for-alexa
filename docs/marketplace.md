# Marketplace-Installation — TAFA-Integration 0.4.2

[English](en/marketplace.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Marketplace und Home Assistant Apps sind unterschiedliche Installationswege. Die empfohlene Lösung für CPU-Piper, Whisper und das TAFA Control Center zusammen ist die **[Installation einer einzigen App](app.md)**. **Beide Wege nicht auf demselben Home Assistant installieren.**

## Umfang der Marketplace-Integration

Marketplace installiert die zusammengeführte HA-Integration `tablet_assist_for_alexa` **0.4.2** mit STT, TTS, Gesprächsrouter, optionalen Durchsagen, nativer Rufwort-Geräteregistrierung, Multiroom/Room-Audio-Kompatibilitätsschnittstellen sowie optionaler Kamera-/Bewegungs- und Vision-Unterstützung. Die alte separate `jarvis_tablet_audio`-Integration ist bei einer Neuinstallation **nicht erforderlich**. Device Bridge 1.0.0 bleibt eine unveränderte Android-App.

Marketplace kann keine laufenden CPU-Sprachdienste installieren. Bei alleiniger Marketplace-Einrichtung benötigst du einen bestehenden kompatiblen Piper-HTTP-Server (`/health`, `/synthesize`) sowie eine Wyoming-STT-Entität oder die kompatible Schnittstelle `/stt` auf demselben Server. [CPU-Sprachserver](proxmox.md) · [GPU-Worker](worker.md). Die **TAFA Home-Assistant-App** enthält Piper und Whisper für CPU bereits selbst.

## Einrichtung über Marketplace

1. Home Assistant sichern und möglichst eine Testinstallation verwenden. Ziel: Home Assistant Core ab 2026.11.
2. Einstellungen → Marketplace → Über Link hinzufügen: `https://github.com/michaelbudisch/tablet-assist-for-alexa`, Kategorie Integration.
3. Installieren und bei Bedarf Home Assistant neu starten.
4. Einstellungen → Geräte & Dienste → Integration hinzufügen → **TAFA**.
5. Erreichbare Piper-Adresse eintragen; optional Wyoming-STT, GPU-Worker, KI-Agent und Durchsagen konfigurieren.
6. Assist-Pipeline mit TAFA STT, Gesprächsrouter und TTS erstellen/auswählen. Die Pipeline in Home Assistant Assist oder der HA Companion App auswählen, nicht in der Device Bridge.

[In HA öffnen](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration) · [Einrichtung starten](https://my.home-assistant.io/redirect/config_flow_start/?domain=tablet_assist_for_alexa)

## Einstellungen

| Feld | Bedeutung |
|---|---|
| Piper-Adresse | Kompatible lokale Piper-HTTP-API, z. B. `http://speechserver.local:5000` |
| CPU-STT-Entität | Optionale Wyoming-STT-Entität; ohne diese wird `/stt` am Piper-Server verwendet |
| GPU-Streaming-Adresse | Optionales externes Qwen-Streaming im privaten LAN; kein zusätzlicher API-Schlüssel |
| GPU-STT-Entität/Host | Optionale Beschleunigung mit CPU-Reserve |
| Konversationsagent | Optionaler bestehender HA-Agent für allgemeines Wissen |
| Klangprofil und Stimme | Optionale Einstellungen |
| MP3-Durchsagen | Optionale HTTPS-MP3-Erzeugung und Raumzuordnung |

Keine manuelle YAML-Konfiguration und kein privates Dashboard nötig. Die Oberfläche ist DE/EN, Standard-Sprachbefehle und CPU-Modelle sind Deutsch. Die Android-App verwaltet Kamera-/Mikrofonberechtigungen und Wakeword-Aktivierung eigenständig.

## Altinstallationen, Updates und Grenzen

- Eine bestehende `jarvis_tablet_audio`-Installation nicht überschreiben. Die neue Integration erkennt alte Konfigurationseinträge und vermeidet doppelte API-/Dienst-Registrierungen. Bestehende Raumzuordnungen und Speicherstände werden **nicht** automatisch übernommen.
- Eine durch die TAFA-App verwaltete Integration nicht parallel über Marketplace aktualisieren. Bei Marketplace-Installation Updates ausschließlich dort durchführen.
- Version **0.4.2** vereinheitlicht öffentliche Native-Relay-Komponenten; das private Haushalts-Dashboard bleibt ausgeschlossen. Optionale GPU-Dienste bleiben extern.
- Automatisierte Tests für Code, HACS/hassfest und HA-Laufzeit sind vorhanden. Der reale Test mit Device Bridge, Bluetooth, zwei Tablets und eine komplette neue HA-OS-Installation stehen noch aus. Deshalb **Release-Kandidat**, kein bestätigter stabiler Release.

[App-Installation](app.md) · [Backend](backend-roadmap.md) · [Sicherheit](security.md) · [Multiroom](../homeassistant/examples/MULTIROOM.de.md).
