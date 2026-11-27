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
