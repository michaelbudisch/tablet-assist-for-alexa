# TAFA Device Bridge 1.3.0

- **Verbinden** startet den gewählten Mikrofonmodus und bei ausdrücklicher Freigabe die Kamera. Das Offline-Rufwortmodell wird bei Bedarf einmalig geladen. **Trennen** behält die Auswahl für die nächste Verbindung.
- Android-Paketkennung, Namespace, Java-Quell- und Testpakete sowie interne Aktionen auf `de.tafa.devicebridge` umgestellt.
- Die bisherige App `de.jarvis.audio` muss deinstalliert und eine neu signierte APK installiert werden. App-Einstellungen und Zugangsdaten werden nicht übernommen; Tablet in TAFA neu koppeln.
- Rufwörter einschließlich Jarvis und Hey Jarvis bleiben erhalten. Versionscode 33. Signierter Build mit dem bisherigen Zertifikat.

# TAFA Device Bridge 1.2.10

Signierter finaler Annäherungs-Build, Versionscode 31. Enthält die lokale Erkennung aus 1.2.9 mit klar beschrifteter Ausschaltverzögerung. Über die vorhandene App installieren.

# TAFA Device Bridge 1.2.9

- Auf aktuellem Git-Stand 1.2.8 einschließlich lokaler Beendigung stiller Folgefragen aufgebaut.
- Optionaler eigener HA-Sensor Annäherung pro Tablet. Lokale Frontkamera-Gesichtserkennung läuft auf dem bestehenden YUV-Vorschaustrom, unabhängig von Bild-Uploads und Bildbewegung.
- Mindestgesichtsgröße 15–60 %, 800 ms Bestätigung, 20 % Hysterese und 2–10 Sekunden Ausschaltverzögerung; Live-Größenanzeige zum Einstellen.
- Gebündeltes Modell, keine Identifizierung. Kamera muss ausdrücklich gestartet werden. Ohne Frontkamera oder bei Fehler/Stillstand wird der neue Sensor nicht verfügbar; HA lässt Meldungen nach 8 Sekunden ablaufen.
- Android-App 1.2.9 / Versionscode 30. Der mitgelieferte HA-Code 0.4.66 ergänzt die authentifizierte Geräteschnittstelle und den neuen Sensor. Python-Änderungen benötigen einen HA-Neustart.

# TAFA Device Bridge 1.2.7

Signiertes Update mit der bisherigen Signatur, App-ID de.jarvis.audio und Versionscode 28. Über die vorhandene App installieren.

- Sofortige Auftragsabholung nach nativen Antworten; keine zusätzliche Dauerabfrage. Wartende Aufträge werden auch nach dem Ausgabeende sofort geprüft.
- Die gewählte Sprechendepause gilt jetzt auch für „Immer an“. Vorhandene Einstellungen werden nicht pauschal verkürzt; 1100–1200 ms lassen sich bei Bedarf pro Tablet einstellen.
- Die Ablaufdiagnose zeigt das Wecksignal und trennt Statistiken nach App-Build. Gespeicherte ältere Messungen bleiben verfügbar.
- Die normale Audioabfrage, HA-Auftragswarteschlange und Prüfung des gewählten Audioausgangs bleiben erhalten. Reale Zeitersparnis bitte mit dem nächsten Tablet-Export prüfen.

# TAFA Device Bridge 1.2.6

- Native Zeitdiagnose für Rufwort, manuelle Frage, Folgefrage und Immer an auf Basis des aktuellen GitHub-Stands 1.2.5.
- Eine gemeinsame Tablet-Uhr erfasst Aufnahme, Assist-Ereignisse, Upload, Audioauftrag, Transfer, Decoder, Puffer, Route und Android-Wiedergabefortschritt.
- Sprachende-Latenz, Zeitachse, getrennte P50/P95 und begrenzter lokaler JSON-Export ausschließlich mit Zeitmetadaten.
- Keine zusätzliche HA-Automation oder Diagnoseabfragen; keine Audio-/Gesprächstext-Exporte. Serverphasen enthalten Transport/Wartezeiten, zusätzliche akustische Echo-Verzögerung wird nicht gemessen.
- 68 Unit-Tests, Android Lint, stumme AudioTrack-Fortschrittstests und synthetische DE/EN-Diagnose-/Oberflächentests auf Handy- und Tablet-Emulator. Echte Zeiten müssen nach Installation auf dem Tablet gemessen werden.
- Signiertes Update: TAFA-Device-Bridge-1.2.6.apk, bisheriges Zertifikat, App-ID de.jarvis.audio, Versionscode 27. Über die bestehende App installieren.

# TAFA Device Bridge 1.2.5 — Sofortige Sprachphasen (Quellversion)

**Buildstatus:** Neue Android-Quellversion mit Versionscode **26** und unveränderter App-ID `de.jarvis.audio`. Noch **keine signierte 1.2.5-APK veröffentlicht**. Ein direktes Update der vorhandenen signierten 1.2.4 benötigt das ursprüngliche Signaturzertifikat. Die letzte veröffentlichte signierte APK bleibt 1.2.4.

- **Rufwort:** `detected`, `native_connecting`, `native_listening` und andere Phasen werden beim Wechsel sofort zur authentifizierten HA-Geräte-API übertragen.
- **Verarbeitung:** `native_transcribing`, `native_thinking`, `native_playing` und die Rückkehr zur Bereitschaft werden ereignisgesteuert gemeldet.
- **Kein Audio-Blockieren:** Eine separate Statuswarteschlange führt Netzwerkzugriffe unabhängig von Aufnahme und Benutzeroberfläche aus und fasst bei langsamen Verbindungen veraltete Zwischenstände zusammen.
- **Rückfall:** Der bestehende 12-Sekunden-Statusabgleich bleibt zur Wiederherstellung nach Verbindungsproblemen; er verwendet dieselbe geordnete Warteschlange, damit alte Statusmeldungen nicht spätere überschreiben.
- **Installation:** Mit `build.ps1 -Configuration Release -Check` bauen und mit `sign-release.ps1` unter Verwendung des ursprünglichen Schlüssels signieren. Erst danach kann die neue APK über 1.2.4 installiert werden.
- **Prüfung:** Neue Unit-Tests für Reihenfolge, Zusammenfassung, Fehler und Stoppen von Statusmeldungen. Live-Reaktionszeit auf dem Tablet nach Installation zu überprüfen.

# TAFA Device Bridge 1.2.4

**Signierter Build:** TAFA-Device-Bridge-1.2.4.apk verwendet die bisherige Signatur, App-ID de.jarvis.audio und Versionscode 25. Über die vorhandene App installieren. Prüfung: 49 Unit-Tests, Android Lint ohne Fehler, DE/EN-Oberflächentests im Handy- und Tablet-Emulator sowie 25 Python-Vertrags-/Dokumentationsprüfungen. Echte Bluetooth-/Tablet-Audiotests stehen noch aus.

- **Audioausgabe:** Automatik bevorzugt verbundenes Bluetooth-Medienaudio und verwendet ansonsten den internen Tablet-Lautsprecher. Nur Bluetooth und Nur Tablet bleiben ausdrücklich wählbar.
- **Geprüfte Route:** Streaming und gepufferte Wiedergabe bestätigen den gewählten Ausgang vor der Ausgabe. Bei einem Routenwechsel stoppt die laufende Antwort; die nächste Antwort wählt den aktuellen Ausgang.
- **Kompakte Einstellungen:** Aufklappbare Gruppen, zustandsabhängige Verbinden/Trennen- und Start/Stopp-Schalter. Der Audiomodus kann pro Tablet im aktuellen TAFA Control Center mit Integration 0.4.40 geändert werden.
- **Prüfungen:** Veraltete UI- und Release-Versionsannahmen aktualisiert. Reale Umschaltzeiten und Audiogeräte müssen auf dem Tablet geprüft werden.

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
