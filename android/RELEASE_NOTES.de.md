# TAFA Device Bridge 1.1.0

- Fehlerursachen beim parallelen Decodieren und Abspielen bleiben erhalten; HTTP- und Formatfehler werden nicht durch einen generischen Decoderfehler überlagert.

Die App wurde auf drei klare Hauptbereiche umgestellt:

- **Status** – nur Informationen zu Home Assistant, Bluetooth, aktuellem Audio-/Assist-Zustand, Rufwort, Keepalive, Kamera, Bewegungsschalter und Akku.
- **Verbinden** – Home Assistant suchen, Serveradresse und Token des dedizierten HA-Raumnutzers einrichten. Fehlermeldungen bleiben hier sichtbar.
- **Einstellungen** – alle Bedienoptionen: Audioplayer, Echo-Bluetooth, lautloses Keepalive, Rufwort/Vosk-Modell, Mikrofon/Assist, Display-Freigabe, Kameralinse, Bildintervall, Bewegungserkennung und Kamera-Start/Stopp, Hilfe und Diagnose.

Die separate Kamera-Testvorschau entfällt aus der App. Die Kameraübertragung bleibt ein explizit gestarteter Vordergrunddienst und die Benachrichtigung öffnet nun die Einstellungen. Die Bildbewegung wird weiter als TAFA-Bewegungs-Binärsensor in Home Assistant bereitgestellt, sofern die Kamera mit aktivierter Bewegungsoption Bilder liefert. Der Schalter wirkt auch bei laufendem Kameradienst.

Native Assist, unbegrenzte Folgefragen, das bestehende Bluetooth-Keepalive (mit automatischem Wiederholversuch), Zugangsdatenverschlüsselung und die stabile Gerätekennung bleiben erhalten. Es werden keine Automatisierungen in Home Assistant angelegt oder verändert.

**Signierter Release:** TAFA-Device-Bridge-1.1.0.apk ist mit dem bisherigen Zertifikat signiert. Unveränderte App-ID de.jarvis.audio, Versionscode **20**. Über die vorhandene App installieren, damit verschlüsselte Zugangsdaten und Gerätekennung erhalten bleiben. Tests am echten Echo und Tablet stehen weiterhin aus.
