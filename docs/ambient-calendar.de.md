# Ambient: Familienübersicht und Kalender (TAFA 0.4.67)

In der Ambient-Ansicht öffnet ein kurzer Tipp die Familienübersicht. Die
Kugel bleibt animiert, verkleinert sich und wandert nach oben; ein
türkiser Lichtimpuls begleitet das Einblenden des rollierenden
**Vier-Wochen-Kalenders**. Der HA-Assist-Pfad und die native
Rufworterkennung werden nicht berührt.

**Kalenderquelle:** Keine Zugangsdaten und keine direkte Google-API im
Dashboard. Die Ansicht liest nur mit den Home-Assistant-Berechtigungen des
angemeldeten Benutzers über `calendar.get_events`. Den Google-Kalender
`Familie` zunächst über Home Assistants offizielle Google-Kalender-Integration
hinzufügen; die dann entstehende `calendar.familie` wird automatisch gewählt.
Andere Kalender lassen sich direkt in der Ansicht über **⚙** als
`calendar.xyz` einstellen. Ohne passende Entität erscheinen keine
fiktiven Termine, sondern ein Verbindungshinweis.

**Annäherung / Gesichtserkennung:** Bis zum Android-Update funktioniert
der Tipp bereits. Die native TAFA Device Bridge kann künftig pro Gerät
einen autorisierten HA-Binärsensor ausgeben, z. B.
`binary_sensor.tafa_jarvis_tablet_gesicht_erkannt` zu dem gebundenen
`sensor.tafa_jarvis_tablet_rufwortstatus`. Die Ansicht sucht nur
gerätespezifisch nach `_gesicht_erkannt`, `_berechtigtes_gesicht` oder
`_recognized_face`. Ein allgemeiner Bewegungssensor entsperrt
private Familientermine ausdrücklich nicht automatisch. Für einen anderen
Sensor kann ein Bewohner ihn bewusst in **⚙** eintragen; kein Video oder
Gesichtsbild wird im Dashboard gespeichert.

Alternativ darf eine native Bridge im **eigenen HA-WebView** das Ereignis
`tafa:ambient-presence` mit
`{detail:{device_id:"<paired device ID>",active:true}}` senden.
Ohne ID-Übereinstimmung wird es ignoriert.

Im Display lokal einstellbar: Kalender-Entität, autorisierter
Präsenzsensor und Rückkehrdauer (15–180 s, Standard 55 s).
Bei aktiver Sprache bleibt die Übersicht sichtbar. Kalenderdaten
werden erst beim Öffnen und anschließend höchstens alle fünf Minuten
abgerufen. Es werden keine HA-Automatisierungen verändert.


## Animierter Übergang (0.4.68)

Der Wechsel folgt der Referenzanimation: türkisfarbenes Aufleuchten
der Kugel, kurzlebiger Lichtpfad zum Kalender, kaskadiertes Nachzeichnen
der vier Panelkanten, Scan-Licht, Wetterkarten und Datumskacheln mit
gestaffelter Einblendung und erst danach die Terminchips. Beim Schließen
klappt die Fläche in umgekehrter Reihenfolge zurück.

Die Animation startet ausschließlich bei einer tatsächlichen Öffnung.
Der Lichtpfad zeichnet nur für ca. 0,8 Sekunden und beendet seine
`requestAnimationFrame`-Schleife selbst; bei Schließen und Unmount
werden alle Timer und Frames gelöscht. Die Gerätezustellung, der
Audio-Stream und die native Assist-Pipeline bleiben unberührt.
`prefers-reduced-motion` zeigt die Übersicht ohne Effekt.

Für ältere Tablets werden die animierten Kacheln über
Compositor-Transformationen eingeblendet, keine dauerhaft aktive
Canvas- oder WebGL-Szene hinzugefügt. Beim Nachladen von Terminen
bleibt der Kalender bedienbar; beim Wiederöffnen läuft die Sequenz neu.


## CSS-Isolation (0.4.69)

Die vier Leuchtkanten besitzen die spezifischen Klassennamen
`edge-n`, `edge-e`, `edge-s`, `edge-w`, damit private und
öffentliche Ambient-Dashboards mit ihren allgemeinen
`.top`-Selektoren keine Linien ausblenden können.


## Kalendertermine und Sternschnuppen (0.4.70)

Die Kalender-Ansicht verarbeitet HA `calendar.get_events` über den
WebSocket-Dienst und alternativ das lesende HA-Kalender-REST-API. Der
aktuelle Termin aus `calendar.familie` (`message`, `start_time`,
`end_time`, `all_day`) erscheint unmittelbar als Fallback, falls
Serviceantworten im Gerätebrowser fehlen. Mehrtägige Termine erscheinen
für alle betroffenen Tage; ganztägige Enddaten bleiben exklusiv.

Beim Kalenderaufbau starten **vier Lichtpartikel** von verschiedenen
Kugelpunkten und fliegen in die Kalenderfläche. Danach zeichnen sich
Kalenderrasterlinien auf; Kreuzungspunkte blitzen beim Erreichen auf.
Die Sternschnuppen und Rasterillumination laufen nur für rund zwei
Sekunden. Kein permanentes Rendering, keine Änderungen am Android-Audio.


## Layout wie Referenzvideo (0.4.71)

- Uhr und Datum links oben, vernetzte Kugel als eigener oberer Bereich
  (die bereits vorhandene Sprach- und Kugelanimation läuft unverändert weiter).
- Echte 6-Tage-Vorhersage aus `weather.get_forecasts` mit Symbolen,
  Höchst- und Tiefsttemperaturen. Ohne HA-Daten erscheint ein neutraler
  Platzhalter, keine erfundenen Werte.
- Kompakte Hauswerte mit geprüften Watt-Sensoren für Solar- und
  Netzleistung, Strompreis in ct/kWh und Außentemperatur.
  Datumssensoren werden nie mehr als Solarleistung angezeigt.
- Der rollierende Kalender beginnt sonntags und zeigt 4 Wochen.
  Die Sternschnuppen und Kalender-Rasterlinien erscheinen nur beim
  Öffnen und blenden nach kurzer Zeit **vollständig aus**.
  Kalendertermine und die Hervorhebung des heutigen Tages bleiben.
- Die untere Leiste zeigt den nächsten echten Termin aus `Familie`.
  Eine Nachrichtenschlagzeile wird nicht fingiert, wenn keine
  Nachrichtenquelle eingerichtet ist.
- Pro Gerät bleibt das lokale Zeitfenster und die Präsenzsteuerung
  unverändert; keine HA-Automatisierungen sind Teil dieser Änderung.


## PC-/Tablet-Geometrie (0.4.72)

Der Kalender beginnt auf beiden Bildschirmtypen **erst unterhalb** der
vollständigen Kugel. Der PC nutzt eine geringfügig niedrigere Kugelhöhe
und einen entsprechend tieferen Start der Übersicht; auf Android bleiben
die angepassten Tablet-Proportionen erhalten. Die Uhr bleibt links oben,
der Kalender-Rasteraufbau wird weiterhin wieder transparent.


## Fließender Kugelübergang und transparenter Kalender (0.4.73)

Beim Aufruf bleibt die Sphere im bisherigen DOM-Layout. Vor dem Wechsel
wird aus den verfügbaren Abständen zwischen Uhr, Kugel und Kalender ein
Ziel für `translate3d` und `scale` pro Display berechnet. So schrumpft
die laufende Sphere kontinuierlich, statt durch eine Umschaltung von
`position:relative` auf `position:absolute` zu springen. Beim
Schließen läuft die Transformation zurück. Die native Assist-Pipeline
und die animierte Netzgeometrie bleiben dieselben.

Das Kalenderpanel hat nach der Einblendung keinen permanenten
opak deckenden Hintergrund oder sichtbare Standardzellen mehr.
Wetterleiste und Energiekennzahlen bleiben einzelne halbtransparente
Container. Datumszahlen werden größer, der heutige Tag erhält einen
türkisen Kreis, und Termine erscheinen als schmale türkisfarbene
Streifen. Beim Monatswechsel wird die Monatsabkürzung gesondert
dargestellt. Sternschnuppen und leuchtende Rasterlinien bleiben
auf die kurzlebige Einblendphase beschränkt.

Das Modul behandelt `prefers-reduced-motion` und ändert weder
Mikrofon-Einstellungen noch Home-Assistant-Automatisierungen.

## Geometrie-Fix für Sphere im Kalender (0.4.74)

Beim Umschalten bleibt die Uhr als reguläres Element im Layout;
sie wird nicht mehr plötzlich absolut positioniert. Dadurch
verliert die Sphere keine Layout-Höhe und springt nicht nach oben.
Die Zielgröße beträgt je nach verfügbarer Höhe 50–68 % der
normalen Kugel. Die Position richtet sich nach dem sichtbaren
Kugelradius und hält 14 px Abstand zur Wetterleiste.

Die Uhr behält außerdem ihre normalen Schriftmaße, damit
sich die Höhe ihres Bereichs beim Umschalten nicht verändert.
Die Zielwerte werden vor dem Öffnen aus dem aktuellen
Viewport und den vorhandenen Elementabmessungen berechnet.

Der Fix betrifft nur das optionale Ambient-Frontend;
keine Änderung der Android-Anwendung, des Audio-Routings oder
der Home-Assistant-Automatisierungen.
