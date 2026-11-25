# TAFA Device Bridge · Android 1.0.1 Quellcode-Vorschau

[English](README.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Die Android-Geräteanbindung für TAFA: Home-Assistant-Audio über Bluetooth, optionale lokale Rufworterkennung und Kameraübertragung. Android 9+.

![TAFA Device Bridge](docs/branding/tafa-device-bridge-logo.png)

## Download und Update

Bisher signierter stabiler Build: **TAFA-Device-Bridge-1.0.0.apk**. **Android 1.0.1 liegt noch nicht als signierte Installationsdatei vor. Das CI-Debug-APK darf nicht über die bestehende App installiert werden.**

App-ID de.jarvis.audio, Signatur, Verschlüsselungsalias, Einstellungen, heruntergeladenes Modell und dauerhafte Multiroom-Gerätekennung bleiben erhalten. Der Android 1.0.1 verwendet nach der Signierung Versionscode **14**. Vor dem Update nicht deinstallieren. Home Assistant verwendet weiterhin die vorhandenen Echo-Relay-/Jarvis-Tablet-Audio-Kennungen.

## Einstellungen finden

- **Status:** Audioverbindung, Playersteuerung, Mikrofonstatus und Kamerazugang.
- **Verbinden:** HA-Adresse, Token-QR-Scan, Bluetooth und Raum-Audio; Keepalive liegt in den aufklappbaren Bluetooth-Optionen.
- **Rufwort:** Offline-Modell, Erkennungssteuerung, Gerät/Raum und aufklappbare Feineinstellungen.
- **Hilfe:** Einrichtungstipps, Hintergrundbetrieb, Diagnose und Entfernen der Zugangsdaten.

Deutsch und Englisch im Kopfbereich wählen. Ein Bereichswechsel erhält ungespeicherte Eingaben; beim Sprachwechsel bleibt ein ungespeicherter Token ausschließlich im Arbeitsspeicher.

## Einrichten

1. **Verbinden** öffnen. Android und HA ins gleiche Netz bringen. Gefundenen Server auswählen oder die Basisadresse ohne /lovelace und Dashboard-Pfade eingeben.
2. In HA **Profil → Sicherheit → Langlebige Zugriffstoken → Token erstellen** öffnen. **TAFA Device Bridge** als Namen vergeben, **QR-Code generieren** wählen und mit der App scannen. Token und QR-Code erscheinen nur einmal; vor dem Schließen scannen. Manuelles Einfügen ist ebenfalls möglich.
3. Echo oder Bluetooth-Lautsprecher in Android koppeln, Medienaudio aktivieren und normale Wiedergabe testen.
4. **Speichern & Player starten** wählen. Benachrichtigungen erlauben und die Dienstbenachrichtigung aktiv lassen.
5. Für Sprachanfragen zum kompatiblen TAFA-/Echo-Relay-Dashboard zurückkehren. Die APK richtet HA nicht automatisch ein.

HTTPS prüft das Serverzertifikat. Lokales HTTP erfordert ausdrückliche Freigabe für die genaue lokale IP und den Port; Token, Audio und freigegebene Kamerabilder werden dann unverschlüsselt im LAN übertragen. Ein Adresswechsel setzt die Freigabe zurück.

## Optionale Sprache und dynamisches Multiroom

Unter **Rufwort** das etwa 45 MB große deutsche Vosk-Modell ausdrücklich herunterladen und beim Start Mikrofonzugriff erlauben. Hey Jarvis, Jarvis, Alexa oder alle drei wählen. Die Benachrichtigung bietet Stoppen. Die Erkennungs-Audiodaten bleiben lokal; nur ein Rufwort-Ereignis geht an HA.

Die dynamische API aus 0.9.0 bleibt erhalten: Jede Installation hat eine dauerhafte zufällige Kennung. Raumname vergeben, Erkennung starten und das Gerät in TAFA unter **Sprache & Audio** auswählen/zuordnen. Es gibt keine begrenzten nummerierten Slots. Passende HA-Integration und TAFA-Dashboard werden separat benötigt.

Feineinstellungen steuern Bestätigungen (1–3), Sperrzeit (3–30 s) und Mikrofon-Übergabe (10–90 s). Werte und Stummschaltung werden pro Gerät abgeglichen; bei nicht erreichbaren HA-Einstellungen wird das Mikrofon freigegeben. Ein dB-Schwellwert ist nicht vorhanden.

Für Whisper STT das kompatible Dashboard geöffnet lassen und dessen konkurrierende Rufworterkennung abschalten. Direkt angehängte Wörter können bei der Übergabe verloren gehen. Alexa kann zugleich einen echten Echo aktivieren. Freihändiger Betrieb bei geschlossenem Dashboard ist nicht gewährleistet.

## Experimentelle native Spracheingabe (1.0.1, optional)

**Die bisherige reine Rufworterkennung bleibt die Voreinstellung.** Für native Sprachunterhaltung:

1. Unter **Verbinden** Multiroom-Audio aktivieren, mit dem bestehenden HA-Benutzer ohne Adminrechte verbinden und den Player starten. Unter **TAFA → Geräte** diesen Benutzer dem Tablet-Audioraum zuweisen; **Sprachausgabe testen** sollte funktionieren.
2. Unter **Rufwort** das lokale Vosk-Modell installieren und die Rufworterkennung starten (Mikrofonberechtigung erforderlich).
3. Im neuen Abschnitt **Native Sprachunterhaltung** die Option **Nach Rufwort vollständige Frage aufnehmen** aktivieren. Wahlweise bis zu zwei Anschlussfragen erlauben und die Sprechpause (900–3200 ms, Standard 1700 ms) anpassen.
4. Über **Native Frage ohne Rufwort testen** den Ablauf Mikrofon → Assist → Antwort testen. Danach „Hey Jarvis“, eine kurze Pause und eine Frage sprechen. Der vorhandene Tablet-/Bluetooth-Player gibt die Antwort aus. TAFA wählt die vollständige Assist-Pipeline **TAFA Lokal** beziehungsweise eine passende STT-/TTS-Pipeline.

Die Android-App sendet 16-kHz-PCM-Audio über den authentifizierten Home-Assistant-WebSocket **erst nach Rufwort oder manuellem Test**. Vor der Antwort ist das Mikrofon aus; es werden keine Tonaufnahmen gespeichert. Aktivierte Anschlussfragen dürfen das Mikrofon nach einer Antwort bis zu zweimal erneut öffnen und enden bei Stille. Stummschaltung und Stop beenden die Übertragung. Ist die neue Funktion ausgeschaltet, wird wie bisher nur das Rufwort übermittelt. Ein geöffnetes Browser-Dashboard ist für den nativen Modus nicht nötig. Lokales HTTP überträgt Token und Audio unverschlüsselt im LAN; vertrauenswürdiges HTTPS ist vorzuziehen.

**Release-Status:** Erst Quellcode/CI-Kandidat; eine installierbare Android-1.0.1-APK benötigt die **ursprüngliche Signatur** und Hardwaretests. Die App-ID \`de.jarvis.audio\` bleibt gleich, Versionscode 14. Eine unsignierte APK oder das GitHub-CI-Debug-APK **kann die installierte signierte App nicht aktualisieren**. Die vorhandene App nicht deinstallieren und keine Anmeldedaten löschen. Für die Produktion \`build.ps1 -Configuration Release -Check\` nutzen und anschließend \`sign-release.ps1\` mit dem privaten Original-Keystore ausführen.

## Kamera und Bluetooth-Keepalive

Die Kamera unter **Status** öffnen. Auswahl, HA-Übertragung und lokale Vorschau sind getrennte Karten. Beim Verlassen der Vorschau werden lokale Bilder gelöscht; eine ausdrücklich gestartete Übertragung als Vordergrunddienst kann bis zum Stoppen weiterlaufen. Berechtigungen werden bei Bedarf angefragt. Bildintervalle 1/2/3/5/10 Sekunden und optionale Bewegungserkennung bleiben verfügbar.

Keepalive ist standardmäßig aus. Die stille Schleife bei laufendem Player kann Echo-Ansagen nach Leerlauf verringern, aber Alexa-Musik und Akku beeinflussen. Nur eine Keepalive-Quelle gleichzeitig verwenden. Nach Neustart startet nichts automatisch.

## Build und Signatur

JDK 17, Android-Plattform 35 und Build Tools 36.0.0 verwenden. build.ps1 -Configuration Release -Check ausführen, danach sign-release.ps1 mit -KeystorePath und -Alias. Standardausgabe: **dist/TAFA-Device-Bridge-1.0.0.apk**. Das Skript vergleicht das ursprüngliche 0.7.1-Zertifikat; private Schlüssel werden nicht mitgeliefert.

Build, JVM-Tests, Lint und Handy-/Tablet-UI-Instrumentierung werden lokal validiert. Physische Bluetooth- und Mehrgerätetests bleiben nötig. Siehe [Versionshinweise](RELEASE_NOTES.de.md) und [Drittanbieterhinweise](THIRD_PARTY_NOTICES.de.md).

## Oberfläche

![Tablet](docs/tafa-device-bridge-tablet.png)

[Phone](docs/tafa-device-bridge-phone.png) · [Camera](docs/tafa-device-bridge-camera.png)
