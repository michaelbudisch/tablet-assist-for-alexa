# HA Jarvis Echo Relay 0.2.0 · Preview

## Deutsch

- Neues Tablet-/Telefon-Layout mit eigenem Vektor-Icon und verständlichem Player-Status.
- Oberfläche, Einrichtungshilfe und Benachrichtigungen auf Deutsch und Englisch.
- Token-Scan direkt aus dem einmaligen Home-Assistant-Erstellungsdialog.
- Optionaler nativer Bluetooth-Keepalive, standardmäßig aus und unabhängig vom HA-Dashboard.
- HA-Netzwerksuche, lokale HTTP-Freigabe und bestätigtes Bluetooth-Routing bleiben erhalten.

Die APK über die vorhandene App installieren. Die App-ID bleibt `de.jarvis.audio`; Adresse und Token bleiben erhalten. Signierter, nicht debuggbarer Release-Build mit dem bisherigen lokalen Testschlüssel für Update-Kompatibilität. Keine privaten Schlüssel enthalten. Die App benötigt weiterhin den dokumentierten nativen Audio-Helfervertrag.

Build, JVM-Tests, Android-Lint sowie DE/EN-UI-Tests auf einem isolierten Android-Emulator wurden geprüft. Die tatsächliche Keepalive-Wirkung auf Echo-Geräten nach langen Ruhezeiten ist geräteabhängig und noch nicht auf Hardware bestätigt. Nur den App- oder den HA-Keepalive verwenden. Alexa-Musik und Akkuverhalten testen.

## English

- New phone/tablet layout, custom vector icon and readable player status.
- German and English UI, setup help and notifications.
- Scan the one-time QR code directly from the Home Assistant token creation dialog.
- Optional native Bluetooth keepalive, off by default and independent of the HA page.
- Existing HA discovery, per-address local HTTP consent and verified Bluetooth routing remain available.

Install over the existing app to retain credentials. The application ID remains `de.jarvis.audio`. This non-debuggable release APK uses the same local test signing key as earlier builds for update compatibility. Private signing keys are not included. A controller implementing the documented native audio helper contract is still required.

Build, JVM tests, Android lint and German/English emulator UI checks were verified. Echo idle prompts, normal Alexa playback and long-term battery behavior still need target-device testing. Use either the app keepalive or the HA keepalive, not both.
