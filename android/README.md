# TAFA Device Bridge · Android 1.0.0

**English** | [Deutsch](README.de.md) · [Project overview](../README.md)

The Android companion for TAFA: Home Assistant audio through Bluetooth, optional offline wakeword recognition and camera transmission. Android 9+.

![TAFA Device Bridge](docs/branding/tafa-device-bridge-logo.png)

## Download and update

Signed build: **TAFA-Device-Bridge-1.0.0.apk**, with accompanying SHA256SUMS. Install over the existing signed **HA Jarvis Echo Relay** app.

The original application ID de.jarvis.audio, certificate, encryption alias, preferences, downloaded model and persistent multiroom device ID are preserved. Version code increases to **13**. Do not uninstall before updating. The Home Assistant backend continues using its existing Echo Relay / Jarvis Tablet Audio identifiers.

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
5. Return to the compatible TAFA / Echo Relay dashboard for voice requests. The APK does not configure HA automatically.

HTTPS validates the server certificate. Local HTTP needs explicit permission for the precise local IP and port; token, audio and enabled camera images then travel unencrypted on the LAN. Changing the address resets permission.

## Optional voice and dynamic multiroom

Open **Wakeword**, explicitly download the approximately 45 MB German Vosk model and allow microphone access when starting recognition. Choose Hey Jarvis, Jarvis, Alexa or all three. The notification offers Stop. Recognition audio stays local; only a wakeword event is sent to HA.

The dynamic API from 0.9.0 is preserved: each installation has a persistent random ID. Enter a room name, start recognition, then select/pair the device in TAFA under **Voice & Audio**. There are no fixed numbered slots. Matching HA integration and TAFA dashboard are required separately.

Fine-tuning controls confirmations (1–3), cooldown (3–30 s) and microphone handoff (10–90 s). Settings and mute synchronize per device with HA; lost HA settings connectivity releases the recorder. No dB threshold is provided.

Keep the compatible dashboard open for Whisper STT and turn off its competing wakeword detector. Words immediately after the wakeword can be lost during handoff. Alexa may also trigger a physical Echo. Fully hands-free operation with a closed dashboard is not guaranteed.

## Camera and Bluetooth keepalive

Open the camera from **Status**. Selection, HA relay and local preview have separate cards. Leaving preview clears local images; an explicitly started foreground camera relay can continue until stopped. Permissions are requested when required. Image intervals 1/2/3/5/10 seconds and optional motion detection remain available.

Keepalive defaults off. Its silent loop while the player runs may reduce Echo idle announcements, but can affect Alexa music and battery use. Use one keepalive source at a time. Nothing starts automatically after reboot.

## Build and signing

Use JDK 17, Android Platform 35 and Build Tools 36.0.0. Run build.ps1 -Configuration Release -Check, then sign-release.ps1 with -KeystorePath and -Alias. The default output is **dist/TAFA-Device-Bridge-1.0.0.apk**. The script checks the original 0.7.1 certificate; no private signing keys are included.

Build, JVM tests, lint and phone/tablet UI instrumentation are validated locally. Physical Bluetooth and multi-device testing remain necessary. See [release notes](RELEASE_NOTES.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

## Interface

![Tablet](docs/tafa-device-bridge-tablet.png)

[Phone](docs/tafa-device-bridge-phone.png) · [Camera](docs/tafa-device-bridge-camera.png)
