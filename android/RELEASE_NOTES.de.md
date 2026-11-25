# HA Jarvis Echo Relay 0.9.0 · Dynamisches Multiroom

Diese Testversion ersetzt die bisherige Begrenzung auf vier Plätze durch eine dynamische Geräteverwaltung in Home Assistant. Jedes Tablet erhält eine dauerhaft gespeicherte Gerätekennung und einen frei wählbaren Raumnamen. Sobald die native Erkennung gestartet wird, registriert es sich selbst.

Im TAFA-Dashboard unter Jarvis → Sprache & Audio kannst du die Geräteliste aktualisieren, ein Tablet auswählen und diesem Dashboard zuordnen. Für jedes Gerät lassen sich Rufwort, Empfindlichkeit, Sperrzeit, Übergabezeit und Mikrofonstummschaltung separat einstellen. Weitere Tablets sind ohne Slot-Anlage möglich. Die zuletzt zugewiesene Gerätekennung wird auf dem Dashboard gespeichert.

Bei fast gleichzeitig erkannten Rufwörtern wird nur das zuerst beim Server eingehende Gerät für drei Sekunden freigegeben. Es gibt noch keine Schallortung. Die bestehende Echo-Relay-Ausgabe bleibt unverändert.

**Experimenteller Testzweig:** Die neue Version muss auf echten Android-Tablets geprüft werden. Der bisherige Wake Pilot bleibt bis zur Installation unverändert.  Sie ist keine signierte Update-APK der regulären App.

Die APK bleibt bei der bisherigen App-ID `de.jarvis.audio`. Für die direkte Aktualisierung muss sie mit dem originalen Signaturschlüssel aus Version 0.7.1 signiert sein. Der Release-Prozess prüft die Zertifikatsgleichheit.
