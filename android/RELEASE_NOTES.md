# TAFA Device Bridge 1.1.0

The native app now has three focused tabs:

- **Status** – information only: HA, Bluetooth, current player/Assist/wakeword state, keepalive, camera, motion state and battery.
- **Connect** – discover/configure Home Assistant and the dedicated room user's token; connection errors appear here.
- **Settings** – all controls in one place: player, Echo Bluetooth, silent keepalive, wakeword/Vosk model, microphone/Assist, display permission, camera lens, frame interval, motion detection, start/stop, help and diagnostics.

The separate local camera preview/test screen is removed from normal operation. Opt-in camera streaming still requires explicit user start and is shown as a foreground notification opening Settings. Frame-based movement continues to be exposed as a TAFA Home Assistant motion binary sensor while motion reporting is enabled and recent frames exist. The toggle takes effect during streaming.

Native Assist, unlimited follow-ups, automatic Bluetooth keepalive recovery, encrypted credentials and stable device identity are retained. No HA automations are created or changed.

**Signed release:** TAFA-Device-Bridge-1.1.0.apk is signed with the existing certificate. Unchanged de.jarvis.audio application ID, version code **20**. Install over the existing app to preserve encrypted credentials and device identity. Real Echo/tablet testing remains outstanding.
