**Deutsch** | [English](en/security.md) · [Projektübersicht](../README.de.md)

# Datenschutz und Sicherheit

- Lokale Sprachverarbeitung: keine zusätzliche dauerhafte Mikrofonaufnahme im Browser. Native Assist und seine eigenen Debug-/Cache-Einstellungen können dennoch Anfragen speichern. Aufbewahrung in HA prüfen.
- Keine Zugangsdaten, IPs realer Geräte, HA-Konfigurationssicherungen, Audiodateien oder persönliche Stimmen veröffentlichen. Lokale JSON-Dateien, Secrets, venvs und Modelle sind von Git ausgeschlossen.
- LAN-Dienste nicht im Internet freigeben. Wyoming und Piper haben in diesem Entwurf keine eigene Client-Authentifizierung. MP3 und GPU-Synthese verwenden API-Schlüssel; HTTP nur in vertrauenswürdiger Netzumgebung. Für entfernte Nutzung geschützte Verbindungen einsetzen.
- Alexa ist ein optionaler Cloud-Dienst, nicht vollständig lokal. Die Ansage-MP3 ist bei HTTPS-Auslieferung über zufälligen Link bis zu 15 Minuten abrufbar. Keine vertraulichen Inhalte. Reverse Proxy ausschließlich für die Audio-Dateiroute, nicht für die API. Zugriff auf andere Sprachdienste verbieten.
- Automatische Hinweise sind anfänglich ausgeschaltet und dürfen die Ruhezeiten nicht umgehen. Vor produktivem Einsatz eine unabhängige Sicherheitsprüfung durchführen.
