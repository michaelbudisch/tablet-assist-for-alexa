# TAFA: Modularchitektur und Jarvis-Migration

## Zielbild

**Ein zentraler Router, einzeln konfigurierbare Aktionen und ereignisbasierte Automationen.** Nicht mehrere Hausdaten-Router, die dieselbe Frage unterschiedlich beantworten.

```text
TAFA Device Bridge → STT → TAFA Anfrage verarbeiten (Conversation Router)
                               ├─ TAFA Sensor auslesen → Datenquellen-Registry
                               ├─ TAFA Internetsuche → SearXNG / Kontext
                               ├─ TAFA Kamera/Vision → Ring / Qwen
                               ├─ TAFA Geräte steuern → HA erlaubte Geräteaktionen
                               └─ Wissensanfragen → konfigurierter LLM-Agent
                             → TAFA Sprechen → Audio-Routing / CPU-Fallback
                             → TAFA Infobox → Dashboard / Ambient

Home Assistant Auslöser (Ring, Waschmaschine, Wärmepumpe ...)
    → standardisierter TAFA Aktionsaufruf → dieselben Module
```

## Eindeutiger Besitzer je Aufgabe

| Modul | Produkt-API / Zuständigkeit | HA-Automation? |
| --- | --- | --- |
| TAFA Anfrage verarbeiten | TAFA Gesprächsrouter und `tablet_assist_for_alexa.anfrage_verarbeiten` | Nein. Eine einzige Router-Instanz |
| TAFA Sensor auslesen | `tablet_assist_for_alexa.sensor_auslesen` mit semantischem Schlüssel | Nein. HA-Integrationseinstellungen → Datenquellen |
| TAFA Internetsuche | `tablet_assist_for_alexa.internet_suche`, SearXNG und Gesprächskontext | Nein. Gesprächsrouter verwaltet Anschlussfragen |
| TAFA Sprechen / Durchsage | `tablet_assist_for_alexa.announce` (Räume, Ruhezeiten, Fallback) | Nein. Optionaler HA-Skript-Adapter |
| TAFA Infobox | `tablet_assist_for_alexa.infobox_anzeigen`; Ereignis `tafa_infobox_show` | Nein. Optionaler HA-Skript-Adapter |
| TAFA Licht/Gerät steuern | Home-Assistant-Licht-/Schalter-Aktionen mit ausdrücklich freigegebener Entität | Nein. HA-Skript oder native Assist-Intents |
| TAFA Kamera und Vision | `tablet_assist_for_alexa.describe_camera`, Ring-Zuordnung | Nein. Ring-Bewegung ist dagegen Auslöser |
| TAFA Auslöser | HA-Automationen für Geräteereignisse, Kalender, Wetter, Wasch-/Spülmaschine | **Ja** – nur Trigger, Bedingungen und Aufruf eines TAFA-Moduls |

**Sensoren sind ausschließlich lesbar.** `sensor.*` kann nicht sinnvoll geschaltet werden. Für Aktionen stehen `light.*`, `switch.*` und andere dafür vorgesehene HA-Entitätsdomänen zur Verfügung, nur im jeweiligen Berechtigungskontext.

## Trennung zwischen Produkt und Privatkonfiguration

- **Produktcode in GitHub** enthält Fähigkeiten, Schema, Datenquellenschlüssel, event contracts, Tests und Vorlagen. Keine Haushalts-Entitäts-IDs, DynDNS-Ziele, Namen, Zugangsdaten oder Automationen.
- **Home Assistant → TAFA-Datenquellen** enthält die tatsächlichen Entitätszuordnungen pro Installation (z. B. `heizoel`).
- **HA-Kategorien** ordnen bestehende Automationen und Skripte dem TAFA-Bereich zu. Zusätzlich erhalten sie das Label `TAFA`.
- **Alte Jarvis-IDs bleiben vorübergehend als Rückwärtskompatibilität erhalten**; der Anzeigename darf umgestellt werden, aber eine Entity-ID wird erst nach Prüfung *aller* Verbraucher geändert.
- **Nicht gleichzeitig zwei Konversationsauslöser für dieselbe Formulierung aktivieren.** Die alte `jarvis_hausdaten_abfragen` kann die neue TAFA-Datenquelle sonst überholen.

## Migrationsablauf ohne Ausfall

1. Bestehende HA-Router, Automationen, Skripte und Backend-Services inventarisieren; Abhängigkeiten suchen.
2. Die neuen TAFA-Aktionsendpunkte bereitstellen, bestehende IDs und Events zunächst weiter akzeptieren.
3. Eine Funktion nach der anderen umstellen: **lesen, ändern, überprüfen**, keine komplette Massenumbenennung.
4. Für jedes migrierte Szenario messen: Route/Quelle, generierte Antwort, Infobox, Sprachausgabe, Status.
5. Alte Jarvis-Aliasse erst entfernen, wenn alle Verbraucher – Dashboard, Mobile App, HA-Skripte, Automationen, externe Clients und Konfigurationen – nachweislich TAFA nutzen.
6. HA-Entitäten und Konfigurationen auf privaten Installationen getrennt von öffentlichen Releases erhalten.

## Warum die Heizölfrage nicht zuverlässig war

Die lokale alte Automation `automation.jarvis_hausdaten_abfragen` liest in einem von 32 Satz-Zweigen den nicht verfügbaren Tankuhren-Abgleich. Die bereits korrekt konfigurierte TAFA-Datenquelle `sources.heizoel` zeigt dagegen auf den Shelly-basierten Bestandswert. Vorverarbeitung durch HA-Satzautomationen kann den zentralen TAFA-Router umgehen.

**Korrekturprinzip:** Die alte Satz-Automation ruft für Heizöl künftig dieselbe semantische Quelle `heizoel` über `sensor_auslesen` auf; danach wird die ganze Satzsammlung modularisiert. Die Bestandszahl ist ein aus Referenzstand minus Verbrauch geschätzter Wert, keine geprüfte Messung aus dem Tank.

## Offene Freigabetests

- Quellstand statisch prüfen und neue Service-Registrierung nach Neustart auf einer HA-Testinstallation laden.
- Antwort für den `heizoel`-Schlüssel prüfen; weitere 31 alte Satz-Zweige auf Quellenabgleich prüfen.
- Neue TAFA-Infobox und bestehende Jarvis-Event-Konsumenten parallel verifizieren.
- Bestehende Hausautomationen unverändert lassen, bis ihre einzelnen Verbraucher umgestellt wurden.
- Keine automatisch erzeugten Jarvis-Duplikate und keine Migration von privaten Daten nach GitHub.
