# HA Jarvis Echo Relay 0.7.0 · experimental preview

Optional German Vosk wakeword recognition adds four modes: **Hey Jarvis**, **Jarvis**, **Alexa**, or **all three**. The detector is off by default, requests microphone permission when started, and downloads the approximately 45 MB offline model only on explicit user action. Recognition stays local; only the recognized phrase is forwarded to Home Assistant as `jarvis_android_wakeword`. The foreground notification includes a Stop control.

## Downloads and installation

- `HA-Jarvis-Echo-Relay-0.7.0-preview.apk`: signed, non-debuggable update for `de.jarvis.audio`, version code 9. Install over the existing signed 0.6.0 app to retain settings and token. The existing signing certificate is preserved.
- `HA-Jarvis-Echo-Relay-0.7.0-wakepilot.apk`: separately installable, debuggable **Jarvis Wake Pilot**, app ID `de.jarvis.audio.wakepilot`, version `0.7.0-pilot`. It has separate settings and uses the persistent release signing key. An older CI pilot signed with another key cannot be updated directly.
- `SHA256SUMS-0.7.0`: SHA-256 checksums for both APKs.

In the pilot, enter the HA address/token, download the German model, select a wakeword, and start only native wakeword recognition. Keep audio playback in the existing app to avoid duplicate players.

## Home Assistant handoff and limitations

Use the matching Home Assistant dashboard listener from this source revision. Keep the dashboard visible and turn off its own wakeword detection during initial tests. After a wakeword, the app releases its microphone and pauses for 50 seconds while the dashboard starts its existing Whisper STT pipeline. Speech immediately following the wakeword can be lost during this handoff. Operation with the dashboard closed is not guaranteed; selecting **Alexa** may also activate a physical Echo. There is no automatic start after reboot.

This is an **experimental preview**, not a device-tested replacement for 0.6.0. Model loading, recognition quality, background operation, microphone coexistence and audio handoff still need testing on a real tablet. Version 0.6.0 remains available.

## Build and validation

Android source: `79dcbd8361d6282d32774d666fc8c7d43db7a644` (`feature/native-wakeword-0.7.0`). Built with Java 17 using `:app:assembleRelease :app:assembleDebug`; release lint passed. APK signatures, application IDs, version codes and 16 KB ZIP alignment were verified. Android JVM tests, lint and instrumentation-test compilation passed in the source branch CI. An obsolete HA test fixture was adjusted to the current settings schema; the isolated Home Assistant 2026.11.0 fixture passed all 215 checks. No physical-device test was performed.
