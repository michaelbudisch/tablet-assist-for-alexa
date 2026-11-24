# Jarvis Multiroom – Entwicklungsentwurf

**Nicht produktiv integriert.** Der zentrale GPU-Worker und CPU-Fallback bleiben unverändert. Die erste Phase ist ein reines, getrennt testbares Audioregister für manuell zugewiesene Räume. Keine privaten Dashboard-Module, keine Kamerabilder und keine Live-Konfiguration werden übernommen.

## Architektur

- Home Assistant verwaltet explizit durch einen Administrator freigegebene Relay-Geräte. Eine stabile Geräte-ID ist keine Authentifizierung. Die HA-Identität und gerätegebundene Sitzungsnachweise müssen serverseitig geprüft werden; kein vom Client angegebener Benutzername darf Autorität verleihen. Bevor die Schnittstelle öffentlich wird, müssen Nutzerberechtigungen, Sitzungsrotation, Widerruf und Neustart-Migration getestet sein.
- Relay-App meldet Bereitschaft und verarbeitet Audio nur für die eigene Geräte-ID. Echo bleibt lokal mit dem Tablet verbunden. Keine automatischen Ausweichantworten in fremden Räumen.
- Anfragen tragen Geräte- und Raumkontext, eine einmalige Request-ID und einen gerätespezifischen Gesprächskontext. Ein Gerät beansprucht einen Auftrag einmalig und bestätigt den Wiedergabestart. Veraltete oder beschäftigte Geräte werden nicht angesprochen.
- Anwesenheit kann optional über lokale Bewegungsmelder erfasst werden; keine personenübergreifende Identifikation oder Verfolgung. Kameras und Mikrofonzugriff getrennt und sichtbar steuerbar, Kamerafunktion in privaten Räumen standardmäßig aus. Keine dauerhafte Speicherung von Innenraumaufnahmen.
- Home Assistant und Worker bleiben zentral; die bestehende Einzelgeräteinstallation bleibt Standard, bis der Mehrgerätepfad mit zwei Geräten getestet wurde.

## Reihenfolge

1. Reines Routing-Modul und Tests (dieser Branch).
2. Authentifizierte HA-Geräteverwaltung und gerätegebundene Audiobridge mit expliziter Migration.
3. Android-Client: persistente Geräte-ID, Raumzuordnung, zielgerichtete Audioantworten und Bestätigung.
4. Zwei Geräte testen, darunter Offline-/Busy-Fall, Neustart, parallele Anfragen und Rückfall.
5. Geräteverwaltung im späteren veröffentlichungsfähigen Dashboard. Private Hauszentrale bleibt getrennt.

Keine Änderung am laufenden HA, keine neuen Geräte gekoppelt.
