# Zusammengeführtes TAFA-Backend 0.4.1 — Release-Kandidat

[English](en/backend-roadmap.md)

## Umsetzung

Das bisher unter `homeassistant/custom_components/jarvis_tablet_audio` veröffentlichte Backend wurde in die gemeinsame Domain `custom_components/tablet_assist_for_alexa` übernommen. Das Kompatibilitätspaket `relay/` erhält die vorhandenen authentifizierten REST-Endpunkte der Device Bridge sowie die bisherigen Raum-Ereignisse. Bei einer Neuinstallation gibt es nur eine HA-Integration; Piper und Faster-Whisper laufen als Dienste in der separaten **Home-Assistant-App**, nicht als laufender Dienst im Marketplace-Paket. Das private TAFA-Dashboard wird nicht mitgeliefert.

Die App installiert beim ersten Start die öffentliche HA-Integration, startet eine interne CPU-Sprachschnittstelle und richtet die TAFA-Integration sowie eine eigene Assist-Pipeline `TAFA Lokal` über HA-APIs ein. Von der App verwaltete Updates legen Sicherheitskopien an. Device Bridge 1.0.0 bleibt unverändert.

## Release-Tests und offene Punkte

- Umgesetzt: eine öffentliche HA-Integration, Native-Kompatibilität, Multiroom/Kamera-Module, Piper/Whisper-CPU-App, zweisprachiges Ingress Control Center, Quellcode- und Docker-CI.
- Automatisiert: HA-Laufzeit, HACS/hassfest, Bundle-Vergleich, Sprach-API-Tests und sichere Installer-Updates.
- Auf echter Hardware noch offen: saubere HA-OS-Neuinstallation, Modell-Download, gesamte Sprachkette mit Device Bridge, Echo-Bluetooth-Wiedergabe und gleichzeitiger Multiroom-Betrieb.
- Frühere `jarvis_tablet_audio`-Konfigurationseinträge/Speicherstände/Pipelines werden nicht automatisch migriert. Solange ein alter Eintrag vorhanden ist, verhindert TAFA doppelte native Dienste. Vorhandene Installationen vorher sichern und getrennt umstellen.
- Stabilen Release erst nach HA-OS-/Android-End-to-End-Test erstellen. Private Haushaltsfunktionen gehören nicht zum öffentlichen Paket.

[App-Installation](app.md) · [Marketplace](marketplace.md) · [Release-Checkliste](release.md).
