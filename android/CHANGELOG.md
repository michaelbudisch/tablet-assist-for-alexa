# Android changelog

**English** | [Deutsch](CHANGELOG.de.md) · [Project overview](../README.md)

## 0.9.0 · Unlimited dynamic multiroom devices

- Keep the canonical **HA Jarvis Echo Relay** product name; the side-by-side debug build is **HA Jarvis Echo Relay (Test)**. Continue the main version line (0.7.1 → 0.8.0 → 0.9.0), with 0.9.0 still experimental and not yet an officially signed update.

- No numbered tablet slots. Each Android installation enrolls with a persistent random ID; Home Assistant creates device records and all five settings dynamically.
- TAFA device manager can list, choose, pair, rename, mute and remove devices without manual helper creation.
- Authenticated HA API handles wake events and accepts only the earliest arriving device within a three-second arbitration window.
- Settings are isolated by device ID. Legacy 0.8.0 fixed-slot helpers and routing are no longer used.
- Existing Echo Relay/Room Audio output is unchanged. Real multi-device hardware testing is still required.

## 0.8.0 · Multiroom native wakeword detection

- Each Android tablet gets a persistent random installation ID, its own selectable device slot (1–4) and a user-editable room label.
- Four independent Home Assistant profiles provide mute, phrase, strictness, cooldown and microphone handoff. Each slot is claimed by one installation; conflicting devices fail closed.
- TAFA: select the matching device slot under **Voice & Audio**, click **Pair this tablet**, then say its wakeword. Only the exact paired installation can trigger this dashboard.
- A central HA router accepts only the first wakeword arriving within a 3-second arbitration window, suppressing duplicate responses; this is not sound-distance estimation.
- Top-right microphone mute and app settings are now device-specific. On lost HA connectivity or slot conflicts, the Wake Pilot releases its microphone.
- Existing Echo Relay playback is untouched; room-specific output still requires the existing per-room HA user/Room Audio setup for additional tablets.
- Old shared 0.7.1 helpers remain for legacy clients, but 0.8.0 no longer reads them.

## 0.7.1 · Remote controls for native wakeword

- TAFA/HA: mute with `input_boolean.jarvis_native_wake_stumm` and optionally with the top-right dashboard microphone icon. Muting releases the Android recorder.
- Shared HA helpers for wakeword choice, recognition strictness (1–3 repeated Vosk hypotheses), cooldown (3–30 s) and microphone handoff pause (10–90 s).
- Android app shows and edits all settings; authenticated synchronization with HA updates active detection. There is no calibrated acoustic dB threshold; Vosk does not expose one in the current implementation.
- HA mute sync roughly every 2.5 seconds (full settings roughly every 12 seconds); if HA becomes inaccessible, the microphone fails closed.
- Experimental debug app remains separate from signed stable 0.6.0. Physical Android testing remains necessary.

## 0.7.0 · Experimental native wakeword recognition

- Opt-in German offline Vosk recognition for **Hey Jarvis**, **Jarvis**, **Alexa**, or **all three**. Default: off.
- Download the ~45 MB model explicitly through the app. Microphone service uses Android's visible foreground notification with a Stop action.
- Publish only the matched wakeword as an authenticated Home Assistant `jarvis_android_wakeword` event; microphone audio and transcripts are not uploaded.
- Pause local detection for 50 seconds after wake detection, releasing the microphone for the existing HA/Whisper dashboard pipeline.
- The old audio bridge, camera and Bluetooth player remain unchanged. Requires a live dashboard event listener and physical testing; no signed 0.7.0 APK has been released.

## 0.6.0 · Rooms and camera intervals

- Room-specific audio helpers and camera push using authorized non-admin accounts; existing single-device mode remains available.
- Selectable 1/2/3/5/10-second camera intervals, visible version/build and updated DE/EN setup.
- Signed update APK reuses the existing certificate. Room features separately require HA backend 1.7.0; physical two-tablet validation remains outstanding.

## 0.5.0 · HA camera and local vision
- Add explicit-start background camera delivery with its own Stop notification, normalized JPEGs and authenticated same-origin HA push.
- Add memory-only images, paired sessions/sequences, remote Stop, 15-second image expiry and optional coarse motion detection.
- Add Jarvis Tablet Audio 1.4.0 camera/motion entities, outdoor/door selectors and local vision actions/spoken questions.
- Preserve streaming audio, keepalive, credentials, DE/EN and local camera tests. Add native background/HTTP and real-HA receiver/routing checks before APK publication.

## 0.4.0 · Camera preparation
- Add an optional, explicit-start Camera2 screen with front/rear selection, live preview and on-demand JPEG test images.
- Request camera permission only after Start; explain denial and provide Android settings access when needed.
- Bound output size and retain test images only in memory; clear/close on Stop, screen exit, screen-off and recreation, without automatic restart.
- Preserve independent streaming audio, keepalive, QR scanning and credentials. No network camera endpoint or vision backend is enabled yet.
- Add German/English help and isolated Android checks using emulated cameras.

## 0.3.0 · Streaming
- Decode MPEG Layer III incrementally with Android MediaCodec and play MP3/16-bit PCM WAV through AudioTrack before the HTTP response completes.
- Use a 600 ms startup/rebuffer target and a bounded two-second PCM queue; handle unknown-length streaming WAV and arbitrary network packet boundaries.
- Prime/verify Bluetooth with zeros before submitting speech, preserving the first words; monitor route changes during playback and buffering.
- Spool the same response to private cache for unsupported-format fallback only before speech; never regenerate or replay an answer after partial playback.
- Cancel blocked network reads, delete temporary audio and retain the existing HA command/status helper contract, credentials and keepalive.
- Add timing diagnostics and JVM/native Android tests using synthetic delayed chunked MP3/WAV responses.

## 0.2.0 · HA Jarvis Echo Relay
- Redesign phone/tablet setup with a custom vector icon, three setup cards, readable playback states and expandable diagnostics.
- Add complete English/German interface, setup help and notification localization, including an in-app language switch.
- Document the one-time QR code in the Home Assistant token creation dialog as the primary onboarding path.
- Add opt-in native zero-PCM Bluetooth keepalive, independent of the HA page and off by default.
- Preserve application ID, encrypted credential format and exact-address HTTP consent when upgrading.
- Add emulator UI checks for language switching, responsive layout, consent, token retention, WAV decoding and keepalive cleanup.

## 0.1.2
- Find Home Assistant on the LAN using bounded mDNS/DNS-SD discovery; select discovered addresses in setup.
- Allow HTTP only to private/link-local IP literals after explicit consent for the exact server address; HTTPS certificate verification is unchanged.
- Initialize the media source before requesting Bluetooth, retry the preference after preparation and during muted playback, and accept an already active A2DP route.
- Keep playback muted until the actual Bluetooth route is verified, then monitor the selected output; report route type and preference outcome on failure.

## 0.1.1
- Scan a plain HA access token from a QR code using the embedded camera scanner.
- Request camera access only when scanning; keep manual entry available.
- Validate QR token format and keep scanned tokens masked until the player is started.
- Add an offline QR generator in tools/token-qr.html.

## 0.1.0
- Native Android MediaPlayer prototype, foreground-only opt-in service.
- Authenticated HA polling, Bluetooth route checks, explicit stop, status reporting.
- Initial playback buffers the entire file; streaming is not implemented in this version.
