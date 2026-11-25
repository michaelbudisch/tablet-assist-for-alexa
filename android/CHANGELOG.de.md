# Android-Änderungsverlauf

[English](CHANGELOG.md) | **Deutsch** · [Projektübersicht](../README.de.md)

## 1.0.0 · TAFA Device Bridge

- Neuer Name und freigegebenes Cyan-/Mint-Design mit adaptiven App-Icons.
- Status, Verbinden, Rufwort und Hilfe; gegliederte Kamera und aufklappbare Feineinstellungen.
- Einheitliche Auswahlmenüs, lokalisierte Hilfe und Erhalt des UI-Zustands beim Sprachwechsel.
- Bisherige App-ID und Signatur; Versionscode 13. Dynamisches Multiroom aus 0.9.0 erhalten.

## 0.9.0 · Unbegrenzte dynamische Multiroom-Geräte

- App-Name **HA Jarvis Echo Relay**, bisherige App-ID `de.jarvis.audio` und Versionsfolge `0.7.1 → 0.8.0 → 0.9.0`. Die aktualisierbare Release-APK wird mit dem originalen Zertifikat von 0.7.1 geprüft.

- Keine vordefinierten Tablet-Plätze mehr. Jedes Android-Gerät meldet sich über eine zufällige, eindeutige Installationskennung beim HA-Modul an.
- Home Assistant legt die Gerätedatensätze und alle fünf Einstellungen dynamisch in seiner Speicherdatei an; manuelles Anlegen einzelner Helfer entfällt. Neue Geräte sind direkt in der TAFA-Geräteliste sichtbar.
- Geräte in der Dashboard-Geräteverwaltung auswählen, zuordnen, benennen, separat stummschalten oder bewusst löschen. Ein beliebig neues Tablet kann jederzeit hinzugefügt werden.
- Authentifizierte HA-Schnittstelle verarbeitet Rufwörter und lässt innerhalb von drei Sekunden nur das erste eingehende Ereignis zu. Andere Tablets bleiben still. Die Gerätezuteilung erfolgt pro Dashboard.
- Die alten vier Tablet-Platz-Helfer und das alte Routing der 0.8.0-Testversion werden nicht länger verwendet. Bestehende Echo-Relay-/Room-Audio-Routen bleiben unverändert.
- Noch experimentell: Mehrgeräte-Erkennung und Verhalten auf echten Tablets prüfen.

## 0.8.0 · Native Rufworterkennung mit Multiroom

- Jedes Android-Tablet erhält eine dauerhaft gespeicherte, zufällige Gerätekennung, einen auswählbaren eigenen Tablet-Platz (1–4) und einen frei wählbaren Raumnamen.
- Vier getrennte Geräteprofile in Home Assistant für Stumm, Rufwort, Strenge, Sperrzeit und Mikrofonübergabe; jedes Profil wird mit der ersten Android-Installation, die es aktiviert, verknüpft. Gleiche Plätze auf mehreren Tablets sind gesperrt.
- TAFA: Im Reiter **Sprache & Audio** den passenden Tablet-Platz auswählen, auf **Dieses Tablet koppeln** klicken und das Rufwort auslösen. Das Dashboard speichert die Gerätekennung lokal und verarbeitet nur noch Rufwörter genau dieser Installation.
- Das zentrale HA-Ereignisrouting lässt innerhalb von drei Sekunden nur den zuerst eingetroffenen Rufwort-Kandidaten zu, um Doppelantworten zu verhindern. Es misst keine akustische Entfernung.
- Die native Mikrofon-Stummschaltung oben rechts und die Android-App-Einstellungen arbeiten gerätegetrennt; bei Verbindungsverlust oder belegtem Tablet-Platz gibt der Wake Pilot das Mikrofon frei.
- Die produktive Echo-Relay-Ausgabe bleibt unverändert; für echte raumbezogene Wiedergabe benötigen weitere Tablets weiterhin die bestehende Room-Audio-/Raumkonto-Einrichtung.
- Die bisherigen globalen Helfer aus 0.7.1 bleiben für alte Clients bestehen, werden von 0.8.0 aber nicht mehr verwendet.

## 0.7.1 · Native Rufworterkennung fernsteuern

- TAFA/HA: Stummschaltung über `input_boolean.jarvis_native_wake_stumm` und optional über das Mikrofonsymbol oben rechts im Dashboard. Der Android-Dienst gibt bei Stumm das Mikrofon frei.
- Weitere Home-Assistant-Einstellungen: Rufwort, Erkennungsstrenge (1–3 wiederholte Vosk-Erkennungsergebnisse), Sperrzeit (3–30 s) und Mikrofon-Übergabepause (10–90 s).
- Android-App: alle Werte lokal anzeigen und ändern; authentifizierter Abgleich mit HA. Änderungen werden während der laufenden Erkennung übernommen. Kein akustischer dB-Schwellwert: das Modell stellt dafür keine verlässlich kalibrierte Lautstärkeskala bereit.
- HA-Synchronisierung etwa alle 2,5 Sekunden (weitere Einstellungen alle ca. 12 Sekunden); bei nicht erreichbarem HA wird das Mikrofon aus Datenschutzgründen deaktiviert.
- Veröffentlichung als signierte Release-APK `HA-Jarvis-Echo-Relay-0.7.1.apk` mit bisheriger App-ID und Signatur für Updates von 0.6.0/0.7.0. Der optionale Debug-Pilot bleibt separat. Reale Geräteprüfung erforderlich.

## 0.7.0 · Experimentelle native Rufworterkennung

- Wahlweise lokale deutsche Vosk-Erkennung für **Hey Jarvis**, **Jarvis**, **Alexa** oder **alle drei**. Standardmäßig ausgeschaltet.
- Das ca. 45 MB große Modell wird nur auf ausdrücklichen Knopfdruck geladen. Ein sichtbarer Android-Mikrofon-Dienst hat eine eigene Stopp-Aktion.
- Nur das erkannte Rufwort wird als authentifiziertes Home-Assistant-Ereignis `jarvis_android_wakeword` gesendet; Audiodaten und Transkripte werden nicht übertragen.
- Nach Erkennung 50 Sekunden Mikrofonpause zur Übergabe an die vorhandene HA-/Whisper-Verarbeitung.
- Bluetooth-Ausgabe, Kamera und bestehender Player bleiben unangetastet. Der Dashboard-Empfänger und Hardwaretest sind erforderlich; noch keine signierte 0.7.0-APK veröffentlicht.

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
