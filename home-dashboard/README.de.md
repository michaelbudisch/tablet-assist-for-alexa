# TAFA Home Dashboard · Vorschau 0.1.3

[English](README.md) | **Deutsch** · [TAFA-Projekt](../README.de.md)

Optionale, responsive und konfigurierbare Lovelace-Hauszentrale auf Basis des bisherigen Designs. Sie läuft unabhängig vom bisherigen Kiosk. Es wird keine private Hauskonfiguration mitgeliefert.

## Funktionen

- 14 optionale Module und 39 konfigurierbare Datenrollen mit einer oder mehreren Quellen je nach Rolle.
- Grafischer Karteneditor mit Entitäts-/Einheitenprüfung, Namensvorschlägen, Suchfilter, Modulreihenfolge, Design, Akzentfarbe, Anzeigedichte, Deutsch/Englisch und lokalem Konfigurationsimport/-export.
- Live-Übersicht, PV-Gesamtleistung, Ertrag und Prognose (W/kW sowie Wh/kWh normalisiert), Netzleistung mit wählbarem Vorzeichen und gemessener Energiefluss. Fehlende Messwerte bleiben fehlend; keine überlappenden Zähler zuordnen.
- Licht nach HA-Räumen gruppiert, native Lichtbedienung, Verlaufsdiagramme, ausgewählte Kameravorschauen, Wettervorhersage, Abfallkalender und Einkaufslistenkarten.
- Heizung, Wärmepumpe, Tankfüllstand, Wallbox, Haushaltsgeräte und Speicher über vorhandene HA-Datenquellen.
- Optional integrierte Echo-Relay-Assist-Karte. Sie wird erst nach bewusstem Betätigen von **Assistent laden** auf der Sprachseite eingebunden. Pro Helferpaar nur einen aktiven Echo-Relay-Controller verwenden. Keine automatische Mikrofonaufnahme, Aktion oder Kameraaktivierung auf der Startseite. Kameravorschauen erst bewusst in der Detailansicht öffnen; ausschließlich berechtigte Kameras verwenden.

## Installation

1. Die Dateien `www/tafa-home/dashboard.js` und `www/tafa-home/model.js` aus diesem Verzeichnis nach `/config/www/tafa-home/` kopieren.
2. In HA unter Einstellungen → Dashboards → Ressourcen `/local/tafa-home/dashboard.js?v=0.1.3` als JavaScript-Modul registrieren. Browser vollständig neu laden. Bestehendes Dashboard nicht überschreiben und nicht zwei Versionen der Karte parallel registrieren.
3. Ein separates Dashboard namens TAFA Home Dashboard mit Panel-Ansicht anlegen und eine manuelle Karte hinzufügen:
   ```yaml
   type: custom:tafa-home-dashboard
   version: 1
   modules: []
   bindings: {}
   language: auto
   theme: dark
   density: comfortable
   accent: teal
   gridSign: import
   ```
4. Im Lovelace-Karteneditor Module und passende Datenquellen auswählen. Bedeutung und Einheiten prüfen. Bei Bedarf Konfiguration lokal exportieren. Netz-Vorzeichen korrekt einstellen. Die Karte legt keine Geräte, Helfer oder Automationen an.
5. Optional die TAFA Echo-Relay-Assist-Karte samt Abhängigkeiten anhand der [Dashboard-/Automationsanleitung](../docs/ha-automations.md) installieren. Pipeline-IDs bei Bedarf wählen. Die Startseite startet keine Kamera- oder Mikrofonsitzung.

## Prüfung und Grenzen

`node tests.mjs` mit einer aktuellen Node.js-Version ausführen. Die Tests prüfen Konfiguration, Rollen, fehlende Entitäten, Einheiten, Netz-Vorzeichen, Sprache, HTML-Escaping, native Kartenkonfigurationen und synthetisches HTML. Dateien und Dashboard-Konfiguration sind bereits in einer getrennten HA-Instanz installiert; der optische Test auf einem echten Tablet und eine vollständige Neuinstallation stehen noch aus.

Dies ist eine portable Entwicklungsvorschau und noch kein vollständiger Ersatz des alten Kiosks. Detaillierte Tibber-Kostenrekonstruktion, intelligenter Energieplaner und Geräteprogrammlernen, spezielle Heizungs-/L3-Erkennung, Tankkalibrierung sowie seitenübergreifender Sprachassistent und Infoboxen müssen noch als generische Module übernommen werden. Bestehende Sensoren und Automationen werden nicht ersetzt. Kamera und Sprachausgabe sind bewusst zu aktivieren. Keine echten Zuordnungen oder Backup-Archive öffentlich teilen.
