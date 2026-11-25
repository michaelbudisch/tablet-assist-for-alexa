# TAFA Device Bridge 1.0.1

- **Optional native voice conversation:** Keep existing wake-only behavior by default. After explicit opt-in, detect a wakeword with local Vosk, record 16 kHz PCM in the Android foreground service and stream the complete question into Home Assistant Assist (Whisper → conversation → Qwen/Piper).
- Use the existing, authenticated per-user Multiroom playback service for Bluetooth answers; no open browser or browser HTTPS required for microphone access. On LAN HTTP the app's explicit unencrypted connection consent still applies.
- Two optional short follow-up questions, adjustable 900–3200 ms pause, manual question test button, live native state and remote mute handling.
- Signed release APK **TAFA-Device-Bridge-1.0.1.apk**, version code **14**, with the existing de.jarvis.audio application ID and signing certificate. Install over the existing app to preserve encrypted settings and device identity.
- Full physical Android microphone and Bluetooth end-to-end test is still required.
