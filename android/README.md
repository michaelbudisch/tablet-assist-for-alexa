# TAFA Device Bridge · Android 1.3.0

**1.3.0 (source, APK pending):** New Android package/application ID `de.tafa.devicebridge`. The former `de.jarvis.audio` build cannot be upgraded in-place: uninstall it, then install and connect the newly signed TAFA app, and re-pair this tablet in TAFA Control Center. Existing device settings are not imported automatically. Wakewords such as "Jarvis" and "Hey Jarvis" remain supported.


**English** | [Deutsch](README.de.md) · [Project overview](../README.md)

**1.2.11:** Camera uploads and on-device proximity detection now share physical device orientation, including portrait, reverse portrait and landscape mounting with screen rotation locked. A low-rate sensor listener only runs while the camera is open; uncertain/flat readings keep the last reliable pose and devices without an orientation sensor fall back to display rotation. Turning the tablet resets motion comparison and discards stale face results.

**1.2.10:** Optional independent HA proximity entity using on-device front-camera detection, with adjustable face-size threshold and exit delay. Includes current Git 1.2.8 changes for locally ending silent follow-ups. Install the signed update over the existing app.

Native tablet bridge for Home Assistant: wakeword and Assist, Bluetooth playback, camera and image-motion detection in one compact app. Android 9+.

**First-time setup:** First [configure TAFA in Home Assistant](../docs/en/setup-guide.md), then create a dedicated non-admin HA user for each tablet. Enter the HA base URL and credentials under Device Bridge **Connect**. The signed Android APK is installed separately from the Home Assistant App.

## Native voice diagnostics

Open **Settings → Help & diagnostics → Native voice timeline** for the last 20 native requests. Speech-end latency, a stage timeline, separate P50/P95 cohorts and a local metadata-only JSON export are available. [Native timing guide](docs/native-flow-diagnostics.md).

## Three simple tabs

**Status** shows connections and activity, with **Connect**, **Speak now**, **Start wakeword**, **End conversation** and **Start camera** quick actions. Speak now starts a question without a wakeword; missing credentials open Connect, and a missing wakeword model opens Settings.

**Connect** is for one-time setup: find the target HA server, enter its base URL without dashboard paths, scan/paste the dedicated non-admin HA room user's token, and save/start the connection. Plain HTTP requires explicit per-origin LAN consent.

**Settings** groups detailed controls into **Audio**, **Speech & wakeword**, **Room & device**, **Advanced speech recognition**, **Display & camera** and **Help & diagnostics**. Tap a heading to expand it; only one group opens at a time.

## Audio output in 1.2.4

**Automatic** prefers connected Bluetooth media output and otherwise uses the internal tablet speaker. **Bluetooth only** remains silent without Bluetooth; **Tablet only** uses the internal speaker. A route change stops the current response; the next response selects the current output. TAFA Control Center with integration **0.4.40** can also configure the mode per tablet. Physical Bluetooth and tablet audio testing remains necessary.

## Set up audio and voice

1. In **Connect**, configure the correct Home Assistant server and dedicated room user. The TAFA HA integration must already be configured.
2. For Bluetooth playback, pair the Echo or another media speaker through Android settings. The tablet speaker is also supported.
3. Under **Settings → Audio**, choose Automatic, Bluetooth only or Tablet only, then start playback. The silent keepalive is optional and applies to Bluetooth.
4. Under **Settings → Speech & wakeword**, install the local Vosk model, grant microphone permission, choose the wakeword and start recognition. Spoken requests use native HA Assist.
5. Check live connection and activity in **Status**.

From **1.3.0**, the application ID is `de.tafa.devicebridge`. This is a new installation, not an in-place update of the old Jarvis-package app. Re-enter the Home Assistant connection and pair the device again. Android's optional display permission supports brightness/dimming, not dependable full screen power on/off.

## Microphone mode in 1.2.2

Under **Settings → Speech & wakeword → Native microphone mode**, choose **Muted**, **Wake word** or **Always on**. Home Assistant stores the mode per tablet; TAFA integration **0.4.26 or newer** is required. Always on can start a new request from local sound activity without a wakeword. The current utterance is held only in RAM until speech ends, then passed to Assist in full. The local monitor pauses during recognition and Bluetooth replies. To require a wakeword for each new request, use Wake word with follow-ups disabled.

## Direct HA control in 1.2.3

With TAFA integration **0.4.28**, microphone and conversation settings arrive directly through the authenticated device WebSocket. Without a push connection the app reconciles the state over REST. Switching from Always on to Wake word loads the offline model on demand.

After an applied setting is acknowledged, Control Center can display the measured control round-trip time. The app also reports the active settings channel and its local follow-up ceiling. Actual switching latency needs testing on the tablet.

## Wakeword and follow-up questions

In **Settings → Speech & wakeword → Questions without another wakeword**, the default is **Require wakeword for every question**. Fresh installations start without follow-ups; a previously chosen limit is retained.

Optionally allow **1–100 additional questions per conversation or explicitly opt in to unlimited follow-ups**. For example, 1 allows the original question plus one follow-up. A new wakeword or Speak now starts a fresh conversation. Silence, missing/failed replies, mute or an exhausted limit ends follow-ups. End conversation and local-limit changes also cancel a queued recording. To turn off the microphone entirely, stop the wakeword service or mute the device in HA.

The local limit is a hard ceiling independent of the dashboard. HA may reduce it with its device followup_limit (0 = none, -1 = unlimited on the server), but cannot raise it. The app previously ignored this value. Browser control additionally considers continue_conversation and ends on silence. Native silence detection measures audio levels: background sounds can still be mistaken for speech during an allowed follow-up window. Use the wakeword-only default in noisy rooms.

## Camera and motion

Under **Settings → Display & camera**, select the lens and image interval (1/2/3/5/10 s). Enable **Report image motion** to calculate coarse pixel changes. If the TAFA room is allowed to use its camera in HA and the tablet camera has been explicitly started, the camera uploads still images through the authenticated TAFA room API. HA provides a room camera and a motion binary sensor. The sensor is unavailable without fresh frames or when motion is disabled; it does not identify people or objects.

The separate local preview/test screen was removed. No camera starts automatically, no permanent recording or offline queue is created, and the foreground notification can stop the stream. Respect the privacy of people in view.

## Releases and signing

[Download signed APK 1.2.11](downloads/TAFA-Device-Bridge-1.2.11.apk) · [GitHub release](https://github.com/michaelbudisch/tablet-assist-for-alexa/releases/tag/audio-v1.2.11) · [SHA-256 checksum](downloads/SHA256SUMS). The APK uses the existing certificate, de.jarvis.audio application ID and version code **32**. Install over the existing app to retain credentials and device identity.

For local builds use JDK 17, Android SDK Platform 35 and `build.ps1`; sign with `sign-release.ps1` and the original keystore. The repository contains no private signing keys. Automated tests do not replace real Echo or tablet checks.

[Release notes](RELEASE_NOTES.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

## Near-tablet presence (experimental)

Enable **Settings → Display & camera → Near-tablet presence**, select the **front camera**, then **Start camera**. Start with 25% and four seconds at your normal viewing position. Increase the minimum size if detection reaches too far. Live face-size feedback helps calibration. This estimates proximity from face size rather than measuring metres. Greeting motion remains independent.

The new HA **Annäherung** binary sensor belongs to the enrolled TAFA tablet. Update the included integration and restart HA before testing. Stopped capture or expired reports make it unavailable. Image uploads retain their own interval; no GPU Worker is required.
