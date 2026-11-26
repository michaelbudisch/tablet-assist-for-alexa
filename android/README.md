# TAFA Device Bridge · Android 1.0.3

**English** | [Deutsch](README.de.md) · [Project overview](../README.md)

The Android companion for TAFA: Home Assistant audio through Bluetooth, optional offline wakeword recognition and camera transmission. Android 9+.

![TAFA Device Bridge](docs/branding/tafa-device-bridge-logo.png)

## Download and update

[Download signed APK 1.0.3](downloads/TAFA-Device-Bridge-1.0.3.apk) · [GitHub release](https://github.com/michaelbudisch/tablet-assist-for-alexa/releases/tag/audio-v1.0.3) · [SHA-256 checksum](downloads/SHA256SUMS). Install over the existing signed app.

The original application ID de.jarvis.audio, certificate, encryption alias, preferences, downloaded model and persistent multiroom device ID are preserved. Android 1.0.3 uses version code **16**. Do not uninstall before updating. The connection uses the compatible TAFA/HA device interfaces.

## Find your settings

- **Status:** audio connection, player controls, microphone state and camera shortcut.
- **Connect:** HA address, token QR scan, Bluetooth and room audio; keepalive is inside the expandable Bluetooth options.
- **Wakeword:** offline model, recognition controls, device/room name and expandable fine-tuning.
- **Help:** setup tips, background operation, diagnostics and credential removal.

Choose German or English in the header. Section changes retain unsaved input; a language change retains an unsaved token in memory only.

## Setup

1. Open **Connect**. Keep Android and HA on the same network. Select a discovered server or enter its base URL without /lovelace or dashboard paths.
2. In HA, open **Profile → Security → Long-lived access tokens → Create token**. Name it **TAFA Device Bridge**, choose **Generate QR code** and scan it with the app. HA displays the token and QR code only once; scan before closing. Manual pasting is also available.
3. Pair the Echo or Bluetooth speaker in Android, enable media audio and test normal playback.
4. Press **Save & start player**. Allow notifications and keep the service notification active.
5. Start native voice processing under Wakeword. The APK does not configure the required HA backend automatically.

HTTPS validates the server certificate. Local HTTP needs explicit permission for the precise local IP and port; token, audio and enabled camera images then travel unencrypted on the LAN. Changing the address resets permission.

## Native voice and device control (1.0.3)

Recognition is still explicitly started on the tablet. Under **Wakeword**, download the approximately 45 MB German Vosk model, allow microphone access and choose Hey Jarvis, Jarvis, Alexa or all three. Wakeword recognition stays local; the spoken question is then streamed as 16 kHz PCM to Home Assistant Assist. A browser dashboard is not required.

1. Under **Connect**, configure HA/token and the authenticated per-user room-audio connection. Pair the Bluetooth speaker and start the player.
2. Assign the tablet to the correct user/room in the current TAFA device manager and confirm a test speech output.
3. Start native recognition and ask a question, or use the manual test button. Home Assistant needs a complete Assist pipeline with STT and TTS.
4. Further questions continue until silence, mute or stop. The old two-follow-up limit is removed.

Wakeword, speech pause and digital microphone gain are managed through per-device HA settings. Tablet, battery and Bluetooth status are reported to HA. Each installation retains a persistent random device ID. Mute or Stop ends active microphone streaming; lost HA connectivity releases the recorder.

Optional display control requires explicitly granting Android special access to modify system settings. It adjusts brightness rather than physically powering the screen off.

Compatible current TAFA/HA components are required separately. Explicit local-HTTP consent and unencrypted LAN transmission still apply. Physical microphone, Bluetooth and multi-device testing on real tablets remains necessary.

## Camera and Bluetooth keepalive

Open the camera from **Status**. Selection, HA relay and local preview have separate cards. Leaving preview clears local images; an explicitly started foreground camera relay can continue until stopped. Permissions are requested when required. Image intervals 1/2/3/5/10 seconds and optional motion detection remain available.

Keepalive defaults off. Its silent loop while the player runs may reduce Echo idle announcements, but can affect Alexa music and battery use. Use one keepalive source at a time. Nothing starts automatically after reboot.

## Build and signing

Use JDK 17, Android Platform 35 and Build Tools 36.0.0. Run build.ps1 -Configuration Release -Check, then sign-release.ps1 with -KeystorePath and -Alias. The default output is **dist/TAFA-Device-Bridge-1.0.3.apk**. The script checks the original 0.7.1 certificate; no private signing keys are included.

Build, JVM tests, lint and phone/tablet UI instrumentation are validated locally. Physical Bluetooth and multi-device testing remain necessary. See [release notes](RELEASE_NOTES.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

## Interface

![Tablet](docs/tafa-device-bridge-tablet.png)

[Phone](docs/tafa-device-bridge-phone.png) · [Camera](docs/tafa-device-bridge-camera.png)
