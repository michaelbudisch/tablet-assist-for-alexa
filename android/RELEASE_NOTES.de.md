# HA Jarvis Echo Relay 0.7.1

Signierte Release-APK: **HA-Jarvis-Echo-Relay-0.7.1.apk**. Über die vorhandene signierte App installieren, damit Adresse, Token und Einstellungen erhalten bleiben. App-ID `de.jarvis.audio` und das bisherige Signaturzertifikat bleiben erhalten. Der Versionscode steigt auf **10**. Die APK ist ein nicht debuggbarer Release-Build.

## Änderungen

- Native Mikrofon-Stummschaltung über `input_boolean.jarvis_native_wake_stumm`; dabei wird das Android-Mikrofon freigegeben.
- Rufwort, Erkennungsstrenge (1–3 Bestätigungen), Sperrzeit (3–30 Sekunden) und Mikrofon-Übergabepause (10–90 Sekunden) lassen sich in der App einstellen und mit Home Assistant abgleichen.
- Das erneute Aktivieren nutzt die konfigurierte Übergabepause. HA-Stummschaltung wird etwa alle 2,5 Sekunden, die weiteren Einstellungen etwa alle 12 Sekunden abgefragt. Bei nicht erreichbaren HA-Einstellungen wird das Mikrofon freigegeben.
- Optionale lokale deutsche Vosk-Erkennung: Hey Jarvis, Jarvis, Alexa oder alle drei. Standardmäßig aus; Mikrofonzugriff und Download des etwa 45 MB großen Modells nur auf ausdrückliche Aktion. Kein automatischer Start nach dem Booten.

## Einrichtung und Grenzen

Die [Android-Einrichtung](README.de.md#rufwort--und-mikrofoneinstellungen-071) nennt die fünf benötigten HA-Helfer. Diese sowie einen Dashboard-Empfänger für `jarvis_android_wakeword` separat einrichten; die APK installiert keine HA-Helfer und keinen Dashboard-Code. Ohne Helfer bleibt die native Erkennung stumm. Für Whisper STT das kompatible Dashboard geöffnet lassen und dessen konkurrierende Rufworterkennung ausschalten. Nur der erkannte Rufworttext wird an HA gesendet; die Audiodaten der Erkennung bleiben lokal.

Bluetooth-Player und Kamera bleiben verfügbar. Erkennungsqualität, Hintergrundbetrieb, Audioübergabe und Mikrofon-Koexistenz müssen weiterhin auf einem echten Gerät geprüft werden. Direkt angehängte Wörter können bei der Übergabe verloren gehen. Alexa kann zugleich einen echten Echo auslösen.

## Prüfung

Mit Java 17 aus Android-Quellstand `efaa578af697d4580890405f1f51531302fde383` gebaut. Release-Build, JVM-Tests, Android-Lint und Kompilierung der Instrumentierungstests erfolgreich. APK-Signatur, Paket-/Versionsdaten und 16-KB-ZIP-Ausrichtung geprüft. Eine bereits validierte HA-Testkorrektur für das aktuelle Einstellungsschema ist enthalten. Kein Test auf einem physischen Gerät.
