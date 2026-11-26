# TAFA Device Bridge · Android 1.2.2

**English** | [Deutsch](README.de.md) · [Project overview](../README.md)

Native tablet bridge for Home Assistant: wakeword and Assist, Bluetooth playback, camera and image-motion detection in one compact app. Android 9+.

**First-time setup:** First [configure TAFA in Home Assistant](../docs/en/setup-guide.md), then create a dedicated non-admin HA user for each tablet. Enter the HA base URL and credentials under Device Bridge **Connect**. The signed Android APK is installed separately from the Home Assistant App.

## Three simple tabs

**Status** shows connections and activity, with **Connect**, **Speak now**, **Start wakeword**, **End conversation** and **Start camera** quick actions. Speak now starts a question without a wakeword; missing credentials open Connect, and a missing wakeword model opens Settings.

**Connect** is for one-time setup: find the target HA server, enter its base URL without dashboard paths, scan/paste the dedicated non-admin HA room user's token, and save/start the connection. Plain HTTP requires explicit per-origin LAN consent.

**Settings** has detailed controls: audio player start/stop, Android Bluetooth pairing, silent Echo keepalive, wakeword/model/microphone, native Assist speech pause/manual test, optional display brightness permission, camera lens/interval/motion/start-stop, help and diagnostics. Fine-tuning no longer hides general device settings.

## Set up audio and voice

1. In **Connect**, configure the correct Home Assistant server and dedicated room user. The TAFA HA integration must already be configured.
2. Pair the Echo or another media speaker through Android's Bluetooth settings.
3. Under **Settings → Echo & audio player**, start playback and optionally enable the silent keepalive.
4. Under **Settings → Wakeword**, install the local Vosk model, grant microphone permission, choose the wakeword and start recognition. Spoken requests use native HA Assist.
5. Check live connection and activity in **Status**.

The application ID `de.jarvis.audio`, encrypted credentials, device identity and preferences survive properly signed upgrades. Do not uninstall the previous app if preserving identity matters. Android's optional display permission supports brightness/dimming, not dependable full screen power on/off.

## Microphone mode in 1.2.2

Under **Settings → Native voice conversation → Native microphone mode**, choose **Muted**, **Wake word** or **Always on**. Home Assistant stores the mode per tablet; TAFA integration **0.4.26 or newer** is required. Always on can start a new request from local sound activity without a wakeword. The current utterance is held only in RAM until speech ends, then passed to Assist in full. The local monitor pauses during recognition and Bluetooth replies. To require a wakeword for each new request, use Wake word with follow-ups disabled.

## Direct HA control in 1.2.2

With TAFA integration **0.4.27**, microphone and conversation settings arrive directly through the authenticated device WebSocket. Without a push connection the app reconciles the state over REST. Switching from Always on to Wake word loads the offline model on demand.

## Wakeword and follow-up questions

In **Settings → Native voice conversation → Questions without another wakeword**, the default is **Require wakeword for every question**. Fresh installations start without follow-ups; a previously chosen limit is retained.

Optionally allow **1–100 additional questions per conversation or explicitly opt in to unlimited follow-ups**. For example, 1 allows the original question plus one follow-up. A new wakeword or Speak now starts a fresh conversation. Silence, missing/failed replies, mute or an exhausted limit ends follow-ups. End conversation and local-limit changes also cancel a queued recording. To turn off the microphone entirely, stop the wakeword service or mute the device in HA.

The local limit is a hard ceiling independent of the dashboard. HA may reduce it with its device followup_limit (0 = none, -1 = unlimited on the server), but cannot raise it. The app previously ignored this value. Browser control additionally considers continue_conversation and ends on silence. Native silence detection measures audio levels: background sounds can still be mistaken for speech during an allowed follow-up window. Use the wakeword-only default in noisy rooms.

## Camera and motion

Under **Settings → Camera**, select the lens and image interval (1/2/3/5/10 s). Enable **Report image motion** to calculate coarse pixel changes. If the TAFA room is allowed to use its camera in HA and the tablet camera has been explicitly started, the camera uploads still images through the authenticated TAFA room API. HA provides a room camera and a motion binary sensor. The sensor is unavailable without fresh frames or when motion is disabled; it does not identify people or objects.

The separate local preview/test screen was removed. No camera starts automatically, no permanent recording or offline queue is created, and the foreground notification can stop the stream. Respect the privacy of people in view.

## Releases and signing

[Download signed APK 1.2.2](downloads/TAFA-Device-Bridge-1.2.2.apk) · [GitHub release](https://github.com/michaelbudisch/tablet-assist-for-alexa/releases/tag/audio-v1.2.2) · [SHA-256 checksum](downloads/SHA256SUMS). The APK uses the existing certificate, de.jarvis.audio application ID and version code **23**. Install over the existing app to retain credentials and device identity.

For local builds use JDK 17, Android SDK Platform 35 and `build.ps1`; sign with `sign-release.ps1` and the original keystore. The repository contains no private signing keys. Automated tests do not replace real Echo or tablet checks.

[Release notes](RELEASE_NOTES.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)
