# TAFA Device Bridge · Android 1.1.0

**English** | [Deutsch](README.de.md) · [Project overview](../README.md)

Native tablet bridge for Home Assistant: wakeword and Assist, Bluetooth playback, camera and image-motion detection in one compact app. Android 9+.

## Three simple tabs

**Status** is read-only: HA and Bluetooth connections, current voice/Assist activity, wakeword, keepalive and camera state, plus battery.

**Connect** is for one-time setup: find the target HA server, enter its base URL without dashboard paths, scan/paste the dedicated non-admin HA room user's token, and save/start the connection. Plain HTTP requires explicit per-origin LAN consent.

**Settings** has all controls: audio player start/stop, Android Bluetooth pairing, silent Echo keepalive, wakeword/model/microphone, native Assist speech pause/manual test, optional display brightness permission, camera lens/interval/motion/start-stop, help and diagnostics. Fine-tuning no longer hides general device settings.

## Set up audio and voice

1. In **Connect**, configure the correct Home Assistant server and dedicated room user. The TAFA HA integration must already be configured.
2. Pair the Echo or another media speaker through Android's Bluetooth settings.
3. Under **Settings → Echo & audio player**, start playback and optionally enable the silent keepalive.
4. Under **Settings → Wakeword**, install the local Vosk model, grant microphone permission, choose the wakeword and start recognition. Spoken requests use native HA Assist.
5. Check live connection and activity in **Status**.

The application ID `de.jarvis.audio`, encrypted credentials, device identity and preferences survive properly signed upgrades. Do not uninstall the previous app if preserving identity matters. Android's optional display permission supports brightness/dimming, not dependable full screen power on/off.

## Camera and motion

Under **Settings → Camera**, select the lens and image interval (1/2/3/5/10 s). Enable **Report image motion** to calculate coarse pixel changes. If the TAFA room is allowed to use its camera in HA and the tablet camera has been explicitly started, the camera uploads still images through the authenticated TAFA room API. HA provides a room camera and a motion binary sensor. The sensor is unavailable without fresh frames or when motion is disabled; it does not identify people or objects.

The separate local preview/test screen was removed. No camera starts automatically, no permanent recording or offline queue is created, and the foreground notification can stop the stream. Respect the privacy of people in view.

## Releases and signing

**Version 1.1.0 is available as source and CI debug builds.** A 1.1.0 APK signed with the existing release certificate has **not** been published. In-place updates require the same signing certificate for package `de.jarvis.audio`, version code **20**. Previous signed APKs are listed under [Downloads](downloads/) but are **not** 1.1.0 updates.

For local builds use JDK 17, Android SDK Platform 35 and `build.ps1`; sign with `sign-release.ps1` and the original keystore. The repository contains no private signing keys. Automated tests do not replace real Echo or tablet checks.

[Release notes](RELEASE_NOTES.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)
