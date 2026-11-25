# TAFA Device Bridge 1.0.1 (source candidate — signing required)

- **Optional native voice conversation:** Keep existing wake-only behavior by default. After explicit opt-in, detect a wakeword with local Vosk, record 16 kHz PCM in the Android foreground service and stream the complete question into Home Assistant Assist (Whisper → conversation → Qwen/Piper).
- Use the existing, authenticated per-user Multiroom playback service for Bluetooth answers; no open browser or browser HTTPS required for microphone access. On LAN HTTP the app's explicit unencrypted connection consent still applies.
- Two optional short follow-up questions, adjustable 900–3200 ms pause, manual question test button, live native state and remote mute handling.
- Same Android package id and existing encrypted preferences; versionCode 14. **No public compatible signed APK until the original private keystore is used. Do not relabel the signed 1.0.0 APK.**
- Full physical Android microphone and Bluetooth end-to-end test is still required.

---

# TAFA Device Bridge 1.0.0

Based on Android 0.9.0, source 9cf27e7691a7340f98424ef044583f26528f2546.

- New product name, approved cyan/mint identity, adaptive and monochrome app icon, and notification symbol.
- Status, Connect, Wakeword and Help navigation. Grouped camera controls, expandable advanced settings and consistently themed dropdowns.
- German/English setup guidance; language changes retain the selected section and expanded options. Unsaved tokens remain in memory only.
- Dynamic device identity and per-device HA settings from 0.9.0 retained.

Install TAFA-Device-Bridge-1.0.0.apk over the existing signed app. Original app ID de.jarvis.audio, certificate, encryption alias, device ID and preferences remain; version code 13.

Local validation covers build, JVM tests, lint, phone/tablet UI and signing/package checks. Physical Bluetooth and multi-tablet testing remain outstanding. Matching HA backend and TAFA dashboard are still required.
