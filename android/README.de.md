# TAFA Device Bridge · Android 1.0.5

[English](README.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Die Android-Geräteanbindung für TAFA: Home-Assistant-Audio über Bluetooth, optionale lokale Rufworterkennung und Kameraübertragung. Android 9+.

![TAFA Device Bridge](docs/branding/tafa-device-bridge-logo.png)

## Download und Update

[Signierte APK 1.0.5 herunterladen](downloads/TAFA-Device-Bridge-1.0.5.apk) · [GitHub-Release](https://github.com/michaelbudisch/tablet-assist-for-alexa/releases/tag/audio-v1.0.5) · [SHA-256-Prüfsumme](downloads/SHA256SUMS). Über die vorhandene signierte App installieren.

App-ID de.jarvis.audio, Signatur, Verschlüsselungsalias, Einstellungen, heruntergeladenes Modell und dauerhafte Multiroom-Gerätekennung bleiben erhalten. Android 1.0.5 verwendet Versionscode **18**. Vor dem Update nicht deinstallieren. Die Verbindung nutzt die kompatiblen TAFA-/HA-Geräteschnittstellen.

## Einstellungen finden

- **Status:** Audioverbindung, Playersteuerung, sichtbarer Bluetooth-Keepalive mit Live-Status, Mikrofonstatus und Kamerazugang.
- **Verbinden:** HA-Adresse, Token-QR-Scan, Bluetooth und Raum-Audio.
- **Rufwort:** Offline-Modell, Erkennungssteuerung, Gerät/Raum und aufklappbare Feineinstellungen.
- **Hilfe:** Einrichtungstipps, Hintergrundbetrieb, Diagnose und Entfernen der Zugangsdaten.

Deutsch und Englisch im Kopfbereich wählen. Ein Bereichswechsel erhält ungespeicherte Eingaben; beim Sprachwechsel bleibt ein ungespeicherter Token ausschließlich im Arbeitsspeicher.

## Einrichten

1. **Verbinden** öffnen. Android und HA ins gleiche Netz bringen. Gefundenen Server auswählen oder die Basisadresse ohne /lovelace und Dashboard-Pfade eingeben.
2. In HA **Profil → Sicherheit → Langlebige Zugriffstoken → Token erstellen** öffnen. **TAFA Device Bridge** als Namen vergeben, **QR-Code generieren** wählen und mit der App scannen. Token und QR-Code erscheinen nur einmal; vor dem Schließen scannen. Manuelles Einfügen ist ebenfalls möglich.
3. Echo oder Bluetooth-Lautsprecher in Android koppeln, Medienaudio aktivieren und normale Wiedergabe testen.
4. **Speichern & Player starten** wählen. Benachrichtigungen erlauben und die Dienstbenachrichtigung aktiv lassen.
5. Unter Rufwort die native Sprachverarbeitung starten. Die APK richtet das benötigte HA-Backend nicht automatisch ein.

HTTPS prüft das Serverzertifikat. Lokales HTTP erfordert ausdrückliche Freigabe für die genaue lokale IP und den Port; Token, Audio und freigegebene Kamerabilder werden dann unverschlüsselt im LAN übertragen. Ein Adresswechsel setzt die Freigabe zurück.

## Native Sprache und Geräteverwaltung (1.0.5)

Die Spracherkennung wird weiterhin bewusst auf dem Tablet gestartet. Unter **Rufwort** das etwa 45 MB große deutsche Vosk-Modell herunterladen, Mikrofonzugriff erlauben und Hey Jarvis, Jarvis, Alexa oder alle drei wählen. Die Rufworterkennung läuft lokal; anschließend wird die gesprochene Frage als 16-kHz-PCM an Home Assistant Assist übertragen. Ein Browser-Dashboard ist dafür nicht erforderlich.

1. Unter **Verbinden** HA-Adresse/Token und die benutzergebundene Raum-Audioverbindung einrichten. Den Bluetooth-Lautsprecher koppeln und den Player starten.
2. Das Tablet in der aktuellen TAFA-Geräteverwaltung dem passenden Benutzer/Raum zuordnen und eine Test-Sprachausgabe ausführen.
3. Native Erkennung starten und eine Frage stellen oder die manuelle Testtaste verwenden. Eine vollständige Assist-Pipeline mit STT und TTS muss in Home Assistant eingerichtet sein.
4. Weitere Fragen sind bis Stille, Stummschaltung oder Stopp möglich. Die alte Beschränkung auf zwei Anschlussfragen entfällt.

Rufwort, Sprechpause und digitale Mikrofonverstärkung werden über die gerätebezogenen HA-Einstellungen verwaltet. Tablet-, Akku- und Bluetoothstatus werden an HA gemeldet. Jede Installation behält ihre eigene zufällige Gerätekennung. Stummschaltung oder Stopp beendet aktive Mikrofonübertragung; bei verlorener HA-Verbindung wird das Mikrofon freigegeben.

Die optionale Displaysteuerung benötigt die ausdrücklich erteilte Android-Sonderfreigabe zum Ändern von Systemeinstellungen. Sie regelt die Helligkeit und schaltet den Bildschirm nicht physisch ab.

Passende aktuelle TAFA-/HA-Komponenten werden separat benötigt. Bei lokalem HTTP gelten die ausdrückliche Freigabe und die unverschlüsselte Übertragung weiterhin. Praktische Mikrofon-, Bluetooth- und Mehrgerätetests auf echten Tablets bleiben erforderlich.

## Kamera und Bluetooth-Keepalive

Die Kamera unter **Status** öffnen. Auswahl, HA-Übertragung und lokale Vorschau sind getrennte Karten. Beim Verlassen der Vorschau werden lokale Bilder gelöscht; eine ausdrücklich gestartete Übertragung als Vordergrunddienst kann bis zum Stoppen weiterlaufen. Berechtigungen werden bei Bedarf angefragt. Bildintervalle 1/2/3/5/10 Sekunden und optionale Bewegungserkennung bleiben verfügbar.

Der Keepalive-Schalter ist direkt unter Status beim Player zu finden und standardmäßig aus. Nach Bluetooth-Unterbrechungen, Routenwechseln oder Fehlern versucht er die Wiederaufnahme mit 3–30 Sekunden Abstand. Die stille Schleife bei laufendem Player kann Echo-Ansagen nach Leerlauf verringern, aber Alexa-Musik und Akku beeinflussen. Nur eine Keepalive-Quelle gleichzeitig verwenden. Nach Neustart startet nichts automatisch.

## Build und Signatur

JDK 17, Android-Plattform 35 und Build Tools 36.0.0 verwenden. build.ps1 -Configuration Release -Check ausführen, danach sign-release.ps1 mit -KeystorePath und -Alias. Standardausgabe: **dist/TAFA-Device-Bridge-1.0.5.apk**. Das Skript vergleicht das ursprüngliche 0.7.1-Zertifikat; private Schlüssel werden nicht mitgeliefert.

Build, JVM-Tests, Lint und Handy-/Tablet-UI-Instrumentierung werden lokal validiert. Physische Bluetooth- und Mehrgerätetests bleiben nötig. Siehe [Versionshinweise](RELEASE_NOTES.de.md) und [Drittanbieterhinweise](THIRD_PARTY_NOTICES.de.md).

## Oberfläche

![Tablet](docs/tafa-device-bridge-tablet.png)

[Phone](docs/tafa-device-bridge-phone.png) · [Camera](docs/tafa-device-bridge-camera.png)
