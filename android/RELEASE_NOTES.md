# TAFA Device Bridge 1.2.3

- **WebSocket diagnostics:** The app acknowledges each HA control revision after applying settings, allowing the Control Center to show measured HA-to-device-to-HA round-trip time.
- **Channel telemetry:** Reports WebSocket, authenticated 500-ms polling fallback, or inactive voice service. A working push socket does not send continuous 500-ms HTTP requests.
- **Follow-up diagnostics:** Reports the tablet's local follow-up ceiling so HA can show the effective restrictions. Unlimited follow-ups remain explicit opt-in in Android.
- **Upgrade:** Package `de.jarvis.audio`, version code 24. In-place upgrades require the same original release-signing certificate; a CI debug APK cannot overwrite it.
- Source and automated CI build; live end-to-end latency requires an installed Android 1.2.3 device.

# TAFA Device Bridge 1.2.2

**Signed build:** TAFA-Device-Bridge-1.2.2.apk uses the existing signing certificate, application ID de.jarvis.audio and version code 23. Install over the current app. Validation: 46 JVM tests passed, Android lint without errors, UI-test compilation and three documentation checks. Physical tablet/Echo testing remains outstanding.

- **Instant HA control:** An authenticated, per-enrolled-device Home Assistant WebSocket pushes microphone and conversation settings directly to the tablet.
- **500-ms fallback:** Fast REST reconciliation runs only while the push channel is unavailable; a connected tablet avoids constant HTTP requests.
- **Extended conversations:** Choose 1–100 or opt-in unlimited wakeword-free follow-ups. Silence, errors and mute end the session. HA may restrict each tablet's local ceiling.
- **Wake/continuous switching:** The local wakeword model loads on demand if switching out of Always on.
- **In-place upgrades:** Same Android package `de.jarvis.audio`, version code 23. Use the existing signing certificate to replace an installed release; do not install a separate debug app.
- Signed release; device latency must be tested in the field.

# TAFA Device Bridge 1.2.1

**Signed build:** TAFA-Device-Bridge-1.2.1.apk uses the existing signing certificate, application ID de.jarvis.audio and version code 22. Install over the existing app. Validation: 48 JVM tests passed, Android lint without errors and UI-test compilation. Physical tablet/Echo testing remains outstanding.

- Adds an opt-in native **Always on** speech-activity mode (no wakeword). Local microphone activity starts the existing HA Assist WebSocket, GPU Whisper, Qwen/Piper and Bluetooth output.
- Choose **Muted**, **Wake word** or **Always on** from the app or TAFA Control Center; Home Assistant stores the mode per tablet.
- No background recording files or stored transcripts. A single detected utterance is buffered only in volatile RAM until its end, then sent to Assist in full over the existing authenticated WebSocket. The monitor is stopped for GPU recognition and Bluetooth playback.
- This mode can react to background speech and increases microphone activity. Use Wake word in noisy rooms. Requires TAFA integration 0.4.26 or newer.
- Device Bridge update requires an APK signed with the same signing key as the currently installed app. CI debug builds are not in-place replacements for an existing release-signed APK.

# TAFA Device Bridge 1.2.0

- Status now offers Connect, Speak now, Start wakeword, Start camera and End conversation directly at the top, with a responsive button layout.
- Every question requires a fresh wakeword by default, including upgrades. Optionally choose 1–10 additional questions under Settings → Native Assist.
- The local limit is a hard ceiling. Home Assistant may reduce it, but unlimited server-side follow-ups cannot override it.
- Changing the local limit, ending the conversation or muting cancels queued follow-up recordings. The limit is checked again before opening the microphone.
- Speak now can start native Assist directly after the model, connection, permission and HA mute checks. No dashboard is required.
- Updated German and English setup guidance.

Example: a limit of 1 allows the original question plus one follow-up. Silence, an error or the exhausted limit returns to local wakeword detection. Background sounds can still be mistaken for speech during an explicitly enabled follow-up; use the wakeword-only default in noisy rooms. End conversation leaves local wakeword detection running. To release the microphone, stop or mute the wakeword service.

**Signed update:** TAFA-Device-Bridge-1.2.0.apk uses the existing certificate and application ID de.jarvis.audio, version code 21. Install over the current app to retain credentials, preferences and device identity.

Validation: 45 JVM tests; Android lint without errors; German/English UI smoke tests on phone and tablet emulator layouts. Real Echo/tablet audio and camera testing remains outstanding.
