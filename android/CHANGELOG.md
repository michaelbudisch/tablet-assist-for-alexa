## 1.2.10 · Clearer proximity exit-delay wording
- The proximity setting now labels the timeout as “After … seconds”. Detection behavior and defaults match 1.2.9. Version code 31.

## 1.2.9 · Local near-tablet presence

- Based on current Git 1.2.8, retaining local termination of silent follow-up captures.
- Optional independent per-tablet proximity entity. On-device front-camera face boxes use the existing YUV preview, independent of JPEG delivery and greeting motion.
- Face threshold 15–60%, 800-ms confirmation, 20% hysteresis and 2–10-second exit delay; live face-size feedback for calibration.
- Bundled offline model; no identity recognition. Camera starts explicitly. Wrong lens, errors or stopped capture make the entity unavailable; HA expires reports after eight seconds.
- Android 1.2.9 / version code 30; accompanying HA 0.4.66 adds the authenticated device action and occupancy entity. Python changes require an HA restart.


## 1.2.7 · Faster native audio handoff
- Accepted native audio jobs immediately wake the connected player. Duplicate signals coalesce; the 900-ms poll remains a fallback for external jobs.
- Playback completion immediately checks for waiting jobs. A wakeup cannot reconnect a stopped player.
- Always on uses the same configurable end-of-speech pause as wakeword capture; saved settings are preserved.
- Diagnostics: PLAYER_WAKEUP and BUILD_CODE, build-specific P50/P95 cohorts, backward-compatible history.
- Version code 28, unchanged application ID and original signing certificate. Actual latency improvement requires a new tablet export.

## 1.2.6 · Native device-side latency diagnostics
- Base source updated to GitHub 1.2.5; preserve its live phase telemetry.
- One bounded monotonic timeline per native request, including local capture, Assist events, transfer/decode/buffer/route and actual Android playback progress.
- Match playback by exact job ID, including playback that starts before submit acknowledgement.
- DE/EN viewer, separate successful-run percentiles and metadata-only JSON copy/share; no new server requests or stored audio/text.
- Version code 27, original update certificate. 68 JVM tests, silent AudioTrack presentation checks and dedicated synthetic DE/EN UI checks on phone/tablet; real hardware timing remains to be measured.

## 1.2.5 · Immediate wakeword and Assist phase telemetry
- Native wakeword recognition and each Assist stage now publish HA telemetry on change, rather than waiting up to 12 seconds for the next refresh.
- Dedicated non-blocking worker coalesces obsolete statuses on a slow connection and preserves periodic reconciliation as a fallback.
- Version code 26; signing with the original key remains required for upgrading the installed app. No changes to app ID, audio routing, or HA automations.

# Android changelog

## 1.2.4 · Compact settings and verified audio output
- Automatic audio prefers Bluetooth media output, otherwise the internal tablet speaker. Bluetooth-only and tablet-only modes are available in Android and TAFA Control Center.
- Both streaming and buffered playback verify the selected output before speech; route changes stop the current response.
- Collapsible settings groups and stateful connect/disconnect and start/stop controls.
- Refresh stale UI and component-version test expectations; exercise selections in an expanded settings group.
- Version code 25; original update signing certificate. Validation: 49 JVM tests, Android lint without errors, DE/EN UI smoke on phone and tablet emulators, and 25 Python contract/documentation checks. Physical audio testing remains outstanding.

## 1.2.3 · Device acknowledgement and WebSocket diagnostics
- Acknowledge applied HA control revisions so Control Center can measure per-tablet round-trip time.
- Report WebSocket, REST fallback or inactive service, plus the local follow-up ceiling.
- Ignore events from stale settings sockets after reconnecting.
- Version code 24; signed with the original update certificate.
- Validation: 46 JVM tests, Android lint without errors, UI-test compilation and three documentation checks. Physical tablet/Echo testing remains outstanding.

## 1.2.2 · Instant HA settings and extended follow-ups
- Authenticated per-device HA WebSocket for microphone and conversation settings; immediate acknowledgement and REST reconciliation while disconnected.
- Optional local limits of 1–100 additional questions or explicitly unlimited; HA may reduce the local ceiling. Silence, errors and mute end follow-ups.
- Load the offline wakeword model on demand when switching from Always on.
- Version code 23; signed with the original update certificate.
- Validation: 46 JVM tests, Android lint without errors, UI-test compilation and three documentation checks. Physical tablet/Echo testing remains outstanding.

## 1.2.1 · Three native microphone modes and complete utterance replay
- Device-level Muted / Wake word / Always on selector in Android and TAFA Control Center; requires integration 0.4.26+.
- Optional local sound activity detection without a wakeword. Keep the detected utterance in bounded RAM until speech ends and replay it in full to HA Assist.
- Pause local monitoring during recognition and Bluetooth playback. No recording files or saved transcripts.
- Version code 22; signed with the original update certificate.
- Validation: 48 JVM tests, Android lint without errors and UI-test compilation. Physical tablet/Echo testing remains outstanding.

## 1.2.0 · Quick actions and bounded conversations
- Status quick actions: Connect, Speak now, Start wakeword, End conversation, Start camera.
- Require a wakeword for every question by default, including upgrades from unlimited follow-ups.
- Optional local ceiling of 1–10 additional questions; HA may only reduce it. Respect the previously ignored HA followup_limit.
- Cancel queued follow-up capture on settings changes, mute and conversation end; recheck the effective limit before opening the microphone. Keep wakeword and Assist recorder ownership exclusive.
- Manual questions can explicitly start the foreground service after model, credentials and permission checks; HA mute remains authoritative.
- DE/EN setup guidance, version code 21, original signing certificate.

## 1.1.0 · One settings tab, informative status and focused setup
- **Status:** information only (HA, Bluetooth, wakeword, Assist, camera, keepalive, battery).
- **Connect:** HA discovery, URL, room-user token and save/connection actions only.
- **Settings:** Bluetooth player/keepalive, wakeword/model/mic, native Assist, display permission, camera lens/refresh/motion controls, start/stop, help and diagnostics.
- Remove the separate camera preview/test screen. The camera notification opens Settings. Motion is still reported as a HA motion binary sensor, including while setting changes during live streaming.
- Preserve native Assist audio transport, encrypted credentials, app package ID and existing HA automations.
- Version code 20. An in-place APK update still requires the original release signing certificate.


## 1.0.6 · Unified TAFA room camera
- Replace the legacy Jarvis camera route with the supported authenticated TAFA room-camera API.
- Use the dedicated room user's token, with explicit per-room camera opt-in from TAFA Control Center. No separate Jarvis camera receiver or administrator token is required.
- Update 403/404/409 guidance. Camera remains user-started and temporary; no recordings.
- Version code 19; same package ID, so an in-place update requires the original release signing key.


## 1.0.5 · Visible, self-recovering silent Bluetooth keepalive
- Move the existing optional zero-PCM Bluetooth keepalive from a collapsed advanced menu to the player card on the Status page, with live status.
- Recover automatically after Bluetooth disconnects, audio route changes, transient focus loss and MediaPlayer failures; bounded 3–30 second backoff, preserving the user's enable switch.
- Keep the existing non-audible loop, never change system volume, never request independent audio focus; the native HA Assist/room audio path is unchanged.
- User-controlled and saved per tablet. Runs only with the player service; may reduce but cannot guarantee suppression of Echo “Playing from…” messages.
- App ID unchanged; in-place APK update requires the original Android release signing key.


## 1.0.4 · Auto-enroll when Bluetooth playback is connected
- Starting the native HA Bluetooth player also enrolls the tablet in TAFA's authenticated device registry, even when wakeword recognition has not yet been started.
- While playing audio without the wakeword service, the app sends periodic status heartbeats so the tablet appears online and can be paired/configured in **Apps → TAFA → Devices & multiroom**.
- Enrollment runs on its own worker, with safe retries, and cannot block native Assist or Bluetooth polling; existing wakeword registration remains supported.
- Version code 17 and unchanged package ID. Replacing an installed release requires the existing Android signing certificate.


## 1.0.3 · Native-only HA control

- Unlimited follow-ups until silence, mute or stop. Only the HA Assist / Bluetooth transport is used.
- Remotely controlled pause and digital microphone gain, tablet health and Bluetooth telemetry.
- Opt-in brightness adjustment through Android special permission (not physical screen on/off).
- Version code 16; in-place update requires the existing release signing key.

**English** | [Deutsch](CHANGELOG.de.md) · [Project overview](../README.md)

## 1.0.1 · Native Assist voice conversation

- Optional native Assist streaming after the wakeword; wake-only recognition remains the default.
- Two optional follow-up questions, 900–3200 ms silence endpoint and manual test button.
- Signed update with the existing certificate and version code 14. Physical microphone/Bluetooth testing remains outstanding.

## 1.0.0 · TAFA Device Bridge

- New name and approved cyan/mint identity with adaptive app icons.
- Status, Connect, Wakeword and Help; grouped camera and expandable advanced settings.
- Themed dropdowns, localized guidance and state-preserving language changes.
- Original app ID and signing certificate; version code 13. Dynamic multiroom from 0.9.0 retained.

## 0.9.0 · Unlimited dynamic multiroom devices

- Keep the **HA Jarvis Echo Relay** name, package ID `de.jarvis.audio` and version series `0.7.1 → 0.8.0 → 0.9.0`. An updateable release APK must use the exact 0.7.1 certificate.

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
- Published as signed release APK `HA-Jarvis-Echo-Relay-0.7.1.apk`, with the existing application ID and signing key for updates from 0.6.0/0.7.0. The optional debug pilot remains separate. Physical Android testing remains necessary.

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
