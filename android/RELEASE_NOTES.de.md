# HA Jarvis Echo Relay 0.7.0 · experimentelle Vorschau

Die optionale lokale Vosk-Rufworterkennung bietet vier Modi: **Hey Jarvis**, **Jarvis**, **Alexa** oder **alle drei**. Sie ist standardmäßig aus, fragt den Mikrofonzugriff beim Start an und lädt das etwa 45 MB große deutsche Offline-Modell nur auf Knopfdruck. Die Erkennung bleibt lokal; lediglich das erkannte Rufwort wird als `jarvis_android_wakeword` an Home Assistant gesendet. Die dauerhafte Benachrichtigung bietet eine Stoppen-Schaltfläche.

## Downloads und Installation

- `HA-Jarvis-Echo-Relay-0.7.0-preview.apk`: signiertes, nicht debuggbares Update für `de.jarvis.audio`, Versionscode 9. Über die vorhandene signierte 0.6.0 installieren, damit Einstellungen und Token erhalten bleiben. Das bisherige Signaturzertifikat bleibt erhalten.
- `HA-Jarvis-Echo-Relay-0.7.0-wakepilot.apk`: parallel installierbarer, debuggbarer **Jarvis Wake Pilot**, App-ID `de.jarvis.audio.wakepilot`, Version `0.7.0-pilot`. Eigene Einstellungen und derselbe dauerhafte Signaturschlüssel wie der Release. Ein älterer CI-Pilot mit anderem Schlüssel kann nicht direkt aktualisiert werden.
- `SHA256SUMS-0.7.0`: SHA-256-Prüfsummen für beide APKs.

Im Pilot HA-Adresse/Token eingeben, das deutsche Modell herunterladen, ein Rufwort auswählen und nur die native Erkennung starten. Die Audiowiedergabe weiter über die vorhandene App betreiben, damit keine doppelten Player laufen.

## Home-Assistant-Übergabe und Grenzen

Den passenden Dashboard-Empfänger aus diesem Quellstand verwenden. Das Dashboard geöffnet lassen und dessen eigene Rufworterkennung für erste Tests ausschalten. Nach einem Rufwort gibt die App ihr Mikrofon frei und pausiert 50 Sekunden, während das Dashboard die vorhandene Whisper-STT-Aufnahme startet. Direkt angehängte Wörter können bei dieser Übergabe verloren gehen. Bei geschlossenem Dashboard ist der Betrieb nicht gewährleistet; **Alexa** kann zugleich einen echten Echo aktivieren. Kein automatischer Start nach dem Booten.

Dies ist eine **experimentelle Vorschau**, kein auf dem Gerät getesteter Ersatz für 0.6.0. Modellstart, Erkennungsqualität, Hintergrundbetrieb, Mikrofon-Koexistenz und Audioübergabe müssen auf einem echten Tablet geprüft werden. Version 0.6.0 bleibt verfügbar.

## Build und Prüfung

Android-Quellstand: `79dcbd8361d6282d32774d666fc8c7d43db7a644` (`feature/native-wakeword-0.7.0`). Mit Java 17 und `:app:assembleRelease :app:assembleDebug` gebaut; Release-Lint erfolgreich. Signaturen, App-IDs, Versionscodes und 16-KB-ZIP-Ausrichtung geprüft. Android-JVM-Tests, Lint und Kompilierung der Instrumentierungstests waren im CI des Quellzweigs erfolgreich. Eine veraltete HA-Testdatei wurde an das aktuelle Einstellungsschema angepasst; der isolierte Test mit Home Assistant 2026.11.0 bestand alle 215 Prüfungen. Kein Test auf einem physischen Gerät.
