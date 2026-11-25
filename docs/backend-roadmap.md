# TAFA Backend-Konsolidierung

[English](en/backend-roadmap.md)

## Aktuelle Installation
Marketplace installiert ausschließlich `custom_components/tablet_assist_for_alexa` (0.3.1). Das separate Backend unter `homeassistant/custom_components/jarvis_tablet_audio` wird nicht installiert. Device Bridge 1.0.0 sowie CPU-/GPU-Dienste bleiben eigenständige Installationen.

## Umsetzung und Abnahmekriterien
- Backend-Module in der Marketplace-Domain zusammenführen; erforderliche authentifizierte HTTP-Pfade, Dienste und Ereignisse kompatibel halten. Keine zwei Integrationsordner im Marketplace-Stammverzeichnis.
- Private Hosts und Entitätszuordnungen durch Konfigurationsdialoge ersetzen. Keine Tokens, Haushaltsdaten, Kamerabilder, privaten Dashboards oder Sicherungen veröffentlichen.
- Geräteregistrierung, Raum-Audio, Rufwortweiterleitung, optionale Kamera/Bewegung und Vision, Modellkonfiguration und Durchsagen integrieren. Kamera und Mikrofon benötigen ausdrückliche Freigabe.
- Migration für Altinstallationen mit erhaltenen Kennungen und Raumzuordnungen entwickeln; doppelte Dienste und Provider vermeiden.
- Einrichtung, Entladen, Neuladen, Berechtigungen, Kopplung, Raumtrennung, CPU-Reserve und Worker-Ausfall auf einer sauberen Instanz testen; APK 1.0.0 prüfen.
- Marketplace-Installation und Upgrade über den Repository-Link testen. DE/EN-Anleitungen und Version/Changelog erst bei geprüftem Release entsprechend aktualisieren.

Das private TAFA-Dashboard bleibt ausgeschlossen. Diese Liste ist kein Release und keine Bestätigung einer bereits abgeschlossenen Konsolidierung.
