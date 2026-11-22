# HA Jarvis Echo Relay 0.4.0 · Camera Preparation Preview

## Deutsch

- Optionaler Kamerabereich mit Front-/Rückkamera, lokaler Livevorschau und JPEG-Testbild mit Zeitstempel.
- Kamerazugriff erst nach ausdrücklichem Start. Testbilder liegen nur im Arbeitsspeicher; Stopp und Verlassen der Seite löschen das Bild und schließen die Kamera. Kein automatischer Neustart.
- Deutsche und englische Hilfetexte. Audiostreaming, Bluetooth-Prüfung, Keepalive und gespeicherte HA-Zugangsdaten bleiben erhalten.

**Noch keine Bildübertragung an Home Assistant, kein Kamera-Dauerbetrieb und keine Vision-Auswertung.** Diese Version stellt die lokal testbare Kameragrundlage bereit. Kameraqualität und Orientierung müssen auch auf dem Zieltablet geprüft werden.

Über die vorhandene App installieren, damit Adresse und Token erhalten bleiben. App-ID `de.jarvis.audio`; nicht debuggbarer Release-Build mit demselben bisherigen lokalen Testschlüssel. Keine privaten Schlüssel enthalten.

Geprüft: 22 JVM-Tests und Android-Lint; echter Berechtigungsdialog, Front-/Rückkamera-Vorschau und JPEG-Aufnahme mit emulierten Kameras, Abschalten/Löschen beim Verlassen, DE/EN-Oberfläche sowie die bisherigen nativen MP3/WAV-Streamingtests. Auch die signierte Release-APK hat den Kameratest bestanden.

## English

- Optional camera screen with front/rear selection, local live preview and timestamped JPEG test images.
- Permission is requested only after explicit Start. Images stay in memory; Stop and leaving the screen clear the image and close the camera. No automatic restart.
- German/English help. Streaming audio, Bluetooth route verification, keepalive and saved HA credentials remain available.

**No Home Assistant image delivery, continuous background camera operation or vision inference yet.** This release provides a locally testable camera foundation. Camera quality and orientation also need checking on the target tablet.

Install over the existing app to retain credentials. Application ID `de.jarvis.audio`; non-debuggable release signed with the same previous local test key. Private keys are not included.

Verified: 22 JVM tests and Android lint; actual permission dialog, front/rear preview and JPEG capture with emulated cameras, close/clear on screen exit, German/English UI and the existing native MP3/WAV streaming checks. The signed release APK also passed the camera check.
