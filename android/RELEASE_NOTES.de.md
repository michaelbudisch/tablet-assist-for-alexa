# HA Jarvis Echo Relay 0.9.0 · Dynamisches Multiroom (Testversion)

Diese Testversion ersetzt die bisherige Begrenzung auf vier Plätze durch eine dynamische Geräteverwaltung in Home Assistant. Jedes Tablet erhält eine dauerhaft gespeicherte Gerätekennung und einen frei wählbaren Raumnamen. Sobald die native Erkennung gestartet wird, registriert es sich selbst.

Im TAFA-Dashboard unter Jarvis → Sprache & Audio kannst du die Geräteliste aktualisieren, ein Tablet auswählen und diesem Dashboard zuordnen. Für jedes Gerät lassen sich Rufwort, Empfindlichkeit, Sperrzeit, Übergabezeit und Mikrofonstummschaltung separat einstellen. Weitere Tablets sind ohne Slot-Anlage möglich. Die zuletzt zugewiesene Gerätekennung wird auf dem Dashboard gespeichert.

Bei fast gleichzeitig erkannten Rufwörtern wird nur das zuerst beim Server eingehende Gerät für drei Sekunden freigegeben. Es gibt noch keine Schallortung. Die bestehende Echo-Relay-Ausgabe bleibt unverändert.

**Experimenteller Testzweig:** Die neue Version muss auf echten Android-Tablets geprüft werden. Der bisherige Wake Pilot bleibt bis zur Installation unverändert. Die Debug-App heißt **HA Jarvis Echo Relay (Test)** und ist separat installierbar. Sie ist keine signierte Update-APK der regulären App.
