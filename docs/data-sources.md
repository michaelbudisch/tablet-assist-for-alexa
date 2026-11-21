# Lokale Datenquellen und Sprachbefehle (0.3.0)

[English](en/data-sources.md) · [Installation](marketplace.md)

Die neue Standalone-Integration benötigt keine Helfer oder Entitäten einer fremden Hauszentrale. Unter **Tablet Assist → Datenquellen** siehst du den Konfigurationsstatus. Über den Link zur Integration → **Optionen** kann ein Administrator die eigenen Entitäten auswählen oder wieder abwählen. Alle Felder sind optional. Die Integration wird beim Speichern neu geladen. Private Daten bleiben im lokalen HA-Konfigurationseintrag; die öffentliche Version enthält keine konkrete Haushaltszuordnung.

## Datenquellen

| Funktion | Auswahl / Voraussetzung |
|---|---|
| Wetter | Eine weather-Entität mit aktuellen Daten; Tages- und Stundenprognose abhängig vom Anbieter |
| Einkaufsliste | Eine todo-Entität, z. B. Bring!; zum Hinzufügen/Entfernen muss die Integration diese Aktionen unterstützen |
| Müllabfuhr | Je Müllart ein sensor mit ISO-Datum YYYY-MM-DD im Zustand oder als Datumsschlüssel in Attributen (z. B. Waste Collection Schedule); keine allgemeinen Kalenderentitäten oder bloßen Tage-bis-Abholung-Werte |
| Vorlauf / Rücklauf | °C; Spreizung in K oder °C |
| Strompreis | ct/kWh oder EUR/kWh; günstigster Preis morgen benötigt ein gültiges ISO-Zeitstempel-Attribut timestamp für morgen |
| Netzleistung | W oder kW, positiv Bezug / negativ Einspeisung |
| Solarleistung und Tagesertrag | Aggregierte Leistung W/kW, Energie Wh/kWh; Prognose morgen separat |
| Tagesbezug/Einspeisung | Wh/kWh, jeweils eigene Tageszähler |
| Heizöl | Liter; Bestand und geschätzter Tagesverbrauch separat |
| Waschmaschine, Wärmepumpe, Kühlschrank | Leistung W/kW; Tagesenergie Wh/kWh und verfügbare Kosten in EUR/Cent separat |

Alle Sensoren müssen tatsächlich die gewählte Messgröße liefern. Ein Gesamtsensor kann aus mehreren Quellen über einen HA-Helfer gebildet werden. Unbekannte Zustände oder inkompatible Einheiten erzeugen keine erfundenen Werte. Zeitliche Zuordnung und Aggregation der Sensoren obliegen dem Benutzer. Keine automatische Erstellung von Tarif-, Verbrauchs-, Wetter- oder Müllsensoren.

## Sprachbeispiele (deutsch)

- Nenne mir die aktuelle Vorlauf Temperatur der Heizung.
- Was sagt der Heizungsrücklauf gerade?
- Wie viel Solarstrom haben wir heute produziert?
- Wie wird das Wetter morgen früh? Brauche ich morgen einen Regenschirm?
- Wann wird der nächste Restmüll abgeholt?
- Was haben wir aktuell auf der Bring-Einkaufsliste?
- Setze Milch auf die Einkaufsliste. Streiche Butter von der Einkaufsliste.
- Steht Milch schon auf der Einkaufsliste?
- Erstelle eine Erinnerung. / Erinnere mich morgen um 18 Uhr daran, die Mülltonne rauszustellen.

Bei eindeutigem lokalen Thema wird eine vorhandene Datenquelle abgefragt, nicht das LLM. Mehrdeutige Fragen können eine Rückfrage auslösen. Das ist eine regelbasierte Erkennung, keine allgemeine semantische KI; historische Zeiträume und unbekannte Messgrößen werden nicht unterstützt. Der Marketplace-Assistent und die Sprachmodelle sind weiterhin deutsch; UI und Dokumentation DE/EN.

### Einkaufsliste

Die ausgewählte Liste ist die Standardliste des Routers. Es werden nur ausdrücklich formulierte Einzelartikel-Befehle verarbeitet; kein unscharfes Löschen, keine ganze Liste löschen, keine automatische Aufteilung mehrerer Artikel. Doppelte offene Artikel werden nach exaktem Namen (Groß-/Kleinschreibung ignoriert) vermieden. Nach einer Änderung wird der offene Listeninhalt erneut geprüft. Bring! benötigt weiterhin Internetzugriff. Bei mehreren Assist-Agenten und lokalen Helfern darauf achten, dass die native Assist-Verarbeitung nicht zuvor eine andere Liste auswählt. Für die flexiblen Befehle muss die Anfrage den Tablet-Assist-Gesprächsrouter erreichen.

### Erinnerungen

In den Optionen ausdrücklich aktivieren. Es gibt maximal eine aktive, HA-lokal gespeicherte Erinnerung, also keine Abhängigkeit von Legacy-Helfern. Nach Abholterminen schlägt Jarvis den Vorabend um 18 Uhr vor (falls der Zeitpunkt schon vorbei ist, gegebenenfalls einen Zeitpunkt fünf Minuten in der Zukunft vor der Abholung). Mit Ja bestätigen, Nein ablehnen oder die Uhrzeit etwa mit „Lieber um 19 Uhr“ ändern und erneut bestätigen. Dialogfenster: 60 Sekunden, gleiche Konversation. Eine volle Uhrzeit oder relative Minuten/Stunden/Tage sind möglich. „Welche Erinnerung ist aktiv?“ fragt den Termin ab; „Lösche meine Erinnerung“ verlangt eine Bestätigung. Vorhandene Erinnerungen werden nicht automatisch überschrieben.

Zur Fälligkeit erscheint eine Home-Assistant-Benachrichtigung. Optional kann ein bereits eingerichteter Echo-Raum für die Durchsage gewählt werden; Ruhezeiten und Verfügbarkeit gelten weiterhin. Keine vertraulichen Inhalte, denn Alexa nutzt öffentliche kurzlebige Audio-Links. Benachrichtigungen/Erinnerungen sind gemeinsam sichtbar, nicht personenbezogen. Nach Neustart wird ein überfälliger Termin als HA-Benachrichtigung nachgeholt; nach längerer Verspätung keine Echo-Durchsage. Bei deaktivierten Erinnerungen bleiben gespeicherte Termine pausiert. Beim erneuten Aktivieren werden sie geladen.

## Tests / Grenzen

Die neue Integration und die Legacy-Installation sind getrennt. Die neue Logik wird nur für Marketplace bereitgestellt; bestehende private Installationen werden nicht automatisch migriert. Automatisierte Tests verwenden künstliche Daten, keine echten Einkaufseinträge, Geräte oder Konten. Erforderlich bleibt ein Test mit einem echten HA-System, Bring!-Konto, Wetterintegrationen, Abfallterminen und Android-/Echo-Ausgabe.
