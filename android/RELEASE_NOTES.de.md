# TAFA Device Bridge 1.2.3

**Signierter Build:** TAFA-Device-Bridge-1.2.3.apk verwendet die bisherige Signatur, App-ID de.jarvis.audio und Versionscode 24. Über die vorhandene App installieren. Prüfung: 46 Unit-Tests erfolgreich, Android Lint ohne Fehler, UI-Tests kompiliert und drei Dokumentationsprüfungen bestanden. Ein Praxistest auf Tablet/Echo steht noch aus.

- **WebSocket-Diagnose:** Nach Übernahme einer HA-Einstellung bestätigt die App die Änderungsnummer über ihre authentifizierte Geräteschnittstelle. Das Control Center kann so die echte Steuerungs-Rundlaufzeit anzeigen.
- **Kanalstatus:** Die Statusmeldung unterscheidet WebSocket, HTTP-Fallback und inaktiven Sprachdienst. Der 500-ms-Abgleich bleibt Absicherung, nicht zusätzlicher Datenverkehr bei aktiver Verbindung.
- **Gesprächsmodus:** Die App meldet auch ihre lokale Obergrenze für Anschlussfragen, damit das Control Center korrekt erklärt, ob HA sie weiter einschränkt. Unbegrenzt muss weiterhin ausdrücklich in der App aktiviert werden.
- **Update:** Paket `de.jarvis.audio`, Versionscode 24. Für ein Update über eine bereits signierte Installation ist das ursprüngliche Signaturzertifikat nötig; nicht mit einer fremd signierten Debug-APK überschreiben.
- **Status:** Der native Build wird in GitHub Actions geprüft. Reale Umschaltzeiten sind nur mit installierter 1.2.3 auf einem Tablet messbar.

# TAFA Device Bridge 1.2.2

**Signierter Build:** TAFA-Device-Bridge-1.2.2.apk verwendet die bisherige Signatur, App-ID de.jarvis.audio und Versionscode 23. Über die vorhandene App installieren. Prüfung: 46 Unit-Tests erfolgreich, Android Lint ohne Fehler, UI-Tests kompiliert und drei Dokumentationsprüfungen bestanden. Ein Praxistest auf Tablet/Echo steht noch aus.

- **Sofortige HA-Steuerung:** Die App empfängt Mikrofon- und Gesprächseinstellungen über einen authentifizierten, nur für das registrierte Tablet zugänglichen Home-Assistant-WebSocket. Andere Geräte oder fremde HA-Nutzer können diese Gerätesteuerung nicht abonnieren.
- **Ausfallabsicherung:** Ohne WebSocket wird alle 500 ms der aktuelle Mikrofonstatus abgeglichen. Bei aktiver Push-Verbindung entfällt diese ständige Abfrage; nach einem Neustart werden alle Einstellungen erneut geladen.
- **Längere Gespräche:** In der App sind 1–100 oder unbegrenzte Anschlussfragen auswählbar. „Unbegrenzt“ muss ausdrücklich aktiviert werden; Stille, Fehler und Stumm schalten wieder in die normale Erkennung. In HA lässt sich die Obergrenze pro Tablet verringern.
- **Moduswechsel:** Das lokale Rufwortmodell lädt bei Bedarf, auch wenn der Dienst ursprünglich im Modus „Immer an“ gestartet wurde.
- **Update:** gleiche Android-App-ID `de.jarvis.audio`, Versionscode 23. Zum Überschreiben der bisherigen Installation ist wieder dasselbe Signaturzertifikat erforderlich. Keine neue zweite App installieren.
- **Stand:** Signierter Release; reale Reaktionszeit und Hintergrundnutzung müssen auf dem Tablet geprüft werden.

# TAFA Device Bridge 1.2.1

**Signierter Build:** TAFA-Device-Bridge-1.2.1.apk verwendet die bisherige Signatur, App-ID de.jarvis.audio und Versionscode 22. Über die vorhandene App installieren. Prüfung: 48 Unit-Tests erfolgreich, Android Lint ohne Fehler, UI-Tests kompiliert. Ein Praxistest auf Tablet/Echo steht noch aus.

- **Neuer nativer Mikrofonmodus „Immer an“:** Das Tablet erkennt Sprachaktivität lokal, ganz ohne Rufwort oder zusätzlichen Browser-Whisper-Durchlauf.
- **Vollständige Äußerung:** Die aktuelle Frage wird bis zum Sprechende ausschließlich im Arbeitsspeicher gepuffert und erst dann vollständig an die bestehende Home-Assistant-Assist-Pipeline übergeben. Es wird keine Aufnahmedatei angelegt.
- **Drei Modi:** Stumm / Rufwort / Immer an. Umschaltung direkt in den Android-Einstellungen oder über das TAFA Control Center; die Einstellungen gelten pro Gerät. Home Assistant benötigt die Integration 0.4.26 oder neuer.
- Während KI-Antwort und Bluetooth-Wiedergabe ist die lokale Mikrofonaufnahme unterbrochen. Nach der Ausgabe läuft die Erkennung wieder an.
- **Hinweis:** Im Dauerhörmodus können auch Gespräche, TV oder andere Geräusche unbeabsichtigt TAFA auslösen. Für lautere Umgebungen ist der Rufwortmodus zuverlässiger.
- **Installation:** Die App-ID `de.jarvis.audio` bleibt unverändert; Versionscode **22**. Damit die neue APK über die vorhandene installierbar ist und deine verschlüsselten Zugangsdaten erhalten bleiben, muss sie mit dem *bisherigen privaten Signaturschlüssel* signiert werden. Ein GitHub-CI-Debug-APK ist kein kompatibles In-place-Update.

# TAFA Device Bridge 1.1.0

- Fehlerursachen beim parallelen Decodieren und Abspielen bleiben erhalten; HTTP- und Formatfehler werden nicht durch einen generischen Decoderfehler überlagert.

Die App wurde auf drei klare Hauptbereiche umgestellt:

- **Status** – nur Informationen zu Home Assistant, Bluetooth, aktuellem Audio-/Assist-Zustand, Rufwort, Keepalive, Kamera, Bewegungsschalter und Akku.
- **Verbinden** – Home Assistant suchen, Serveradresse und Token des dedizierten HA-Raumnutzers einrichten. Fehlermeldungen bleiben hier sichtbar.
- **Einstellungen** – alle Bedienoptionen: Audioplayer, Echo-Bluetooth, lautloses Keepalive, Rufwort/Vosk-Modell, Mikrofon/Assist, Display-Freigabe, Kameralinse, Bildintervall, Bewegungserkennung und Kamera-Start/Stopp, Hilfe und Diagnose.

Die separate Kamera-Testvorschau entfällt aus der App. Die Kameraübertragung bleibt ein explizit gestarteter Vordergrunddienst und die Benachrichtigung öffnet nun die Einstellungen. Die Bildbewegung wird weiter als TAFA-Bewegungs-Binärsensor in Home Assistant bereitgestellt, sofern die Kamera mit aktivierter Bewegungsoption Bilder liefert. Der Schalter wirkt auch bei laufendem Kameradienst.

Native Assist, unbegrenzte Folgefragen, das bestehende Bluetooth-Keepalive (mit automatischem Wiederholversuch), Zugangsdatenverschlüsselung und die stabile Gerätekennung bleiben erhalten. Es werden keine Automatisierungen in Home Assistant angelegt oder verändert.

**Signierter Release:** TAFA-Device-Bridge-1.1.0.apk ist mit dem bisherigen Zertifikat signiert. Unveränderte App-ID de.jarvis.audio, Versionscode **20**. Über die vorhandene App installieren, damit verschlüsselte Zugangsdaten und Gerätekennung erhalten bleiben. Tests am echten Echo und Tablet stehen weiterhin aus.
