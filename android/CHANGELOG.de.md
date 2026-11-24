# Android-Änderungsverlauf

[English](CHANGELOG.md) | **Deutsch** · [Projektübersicht](../README.de.md)

## 0.6.0 · Räume und Kamera-Intervalle

- Raumbezogene Audio-Helfer und Raumkamera-Übertragung mit freigegebenen Nicht-Admin-Konten; Einzelgeräte-Modus bleibt erhalten.
- Wählbare Kamera-Intervalle 1/2/3/5/10 Sekunden, Versions-/Buildanzeige und aktualisierte DE/EN-Einrichtung.
- Signierte Update-APK mit bisherigem Schlüssel. Raumfunktionen benötigen separat HA-Backend 1.7.0; Hardwareprüfung auf zwei Tablets bleibt ausstehend.

## 0.5.0 · HA-Kamera und lokale Vision

- Bewusst gestartete Übertragung von Kamerabildern im Hintergrund mit eigener Stopp-Benachrichtigung, normalisierten JPEGs und authentifizierter Übertragung an denselben HA-Server.
- Bilder ausschließlich im Arbeitsspeicher, gekoppelte Sitzungen und Sequenzen, Remote-Stopp, Ablauf nach 15 Sekunden und optionale grobe Bildbewegung.
- Jarvis Tablet Audio 1.4.0 mit Kamera-/Bewegungsentitäten, Außen-/Türkamera-Auswahl, lokalen Vision-Aktionen und Sichtfragen.
- Streaming-Audio, Keepalive, Zugangsdaten, DE/EN und lokale Kameratests bleiben erhalten. Native Hintergrund-/HTTP-Tests sowie reale HA-Empfänger-/Routingtests vor APK-Veröffentlichung.

## 0.4.0 · Kameravorbereitung

- Optionale, bewusst gestartete Camera2-Ansicht mit Front-/Rückkamera, Live-Vorschau und JPEG-Testbildern auf Anfrage.
- Kameraberechtigung nur nach Start anfordern, Ablehnung erklären und bei Bedarf Android-Einstellungen anbieten.
- Bildgröße begrenzen, Testbilder nur im Arbeitsspeicher halten; bei Stopp, Verlassen der Ansicht, Display aus oder Neuerstellung löschen/schließen, ohne automatischen Neustart.
- Unabhängiges Streaming-Audio, Keepalive, QR-Scanner und Zugangsdaten erhalten. Noch kein Netzwerk-Kamera-Endpunkt oder Vision-Backend aktiv.
- Deutsche und englische Hilfe sowie isolierte Android-Prüfungen mit emulierten Kameras.

## 0.3.0 · Streaming

- MPEG Layer III schrittweise mit Android MediaCodec dekodieren und MP3/16-Bit-PCM-WAV vor vollständiger HTTP-Antwort über AudioTrack ausgeben.
- Start-/Nachpufferziel 600 ms und begrenzte Zwei-Sekunden-PCM-Warteschlange; Streaming-WAV unbekannter Länge und beliebige Paketgrenzen behandeln.
- Bluetooth vor Sprachstart mit Nulldaten vorbereiten/prüfen, erste Wörter erhalten, Route während Ausgabe und Pufferung überwachen.
- Dieselbe Antwort im privaten Cache für nicht unterstützte Formate verwenden, nur vor der Sprachausgabe; nach teilweiser Wiedergabe weder neu erzeugen noch wiederholen.
- Blockierte Netzwerklesevorgänge abbrechen, temporäre Audiodaten löschen und bestehenden HA-Befehls-/Statusvertrag, Zugangsdaten und Keepalive erhalten.
- Zeitdiagnose sowie JVM-/native Android-Tests mit synthetischen verzögerten MP3/WAV-Antworten.

## 0.2.0 · HA Jarvis Echo Relay

- Neues Telefon-/Tablet-Layout mit eigenem Vektor-Icon, drei Einrichtungskarten, gut lesbaren Wiedergabestatus und aufklappbarer Diagnose.
- Vollständige deutsche/englische Oberfläche, Einrichtungshilfe und Benachrichtigungen mit Sprachumschaltung.
- Einmaligen Token-QR-Code aus dem HA-Erstellungsdialog als primären Einrichtungsweg dokumentieren.
- Freiwilliger nativer Null-PCM-Bluetooth-Keepalive, unabhängig vom HA-Dashboard und standardmäßig aus.
- App-ID, verschlüsseltes Zugangsdatenformat und HTTP-Zustimmung für die genaue Adresse bei Updates erhalten.
- Emulatorprüfungen für Sprachwechsel, responsives Layout, Zustimmung, Token, WAV-Dekodierung und Keepalive-Bereinigung.

## 0.1.2

- HA-Suche im LAN via begrenztem mDNS/DNS-SD mit Adressauswahl bei der Einrichtung.
- HTTP nur für ausdrücklich freigegebene private/link-lokale IP-Adresse; HTTPS-Zertifikatsprüfung unverändert.
- Medienquelle vor Bluetooth-Anforderung initialisieren; Auswahl nach Vorbereitung und während stummer Wiedergabe erneut versuchen; bereits aktive A2DP-Route akzeptieren.
- Ausgabe bis zur bestätigten Bluetooth-Route stumm halten, gewählten Ausgang überwachen; bei Fehler Route und Auswahlergebnis melden.

## 0.1.1

- HA-Token per QR-Code mit integriertem Kamerascanner erfassen.
- Kamerazugriff nur beim Scannen anfordern, manuelle Eingabe bleibt möglich.
- QR-Tokenformat prüfen und Token bis Player-Start maskieren.
- Offline-QR-Generator unter `tools/token-qr.html`.

## 0.1.0

- Nativer Android-MediaPlayer-Prototyp, explizit aktivierter Vordergrunddienst.
- HA-Abfrage mit Authentifizierung, Bluetooth-Routenkontrollen, expliziter Stopp und Statusmeldungen.
- Vollständiger Dateipuffer; noch kein Streaming.
