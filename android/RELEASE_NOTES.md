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
