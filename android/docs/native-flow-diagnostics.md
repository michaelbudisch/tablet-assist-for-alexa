# Native flow diagnostics · TAFA Device Bridge 1.2.7

Timing is collected and displayed entirely in the native tablet app. No dashboard, extra automation or diagnostic server requests are required.

## Use
Install the APK over the existing app using the original signing certificate. Open **Settings → Help & diagnostics → Native voice timeline**. Local timing metadata is enabled by default. Connect the player, ask through a wakeword or Speak now, and let the reply finish. Select the request, then copy or explicitly share diagnostic JSON as text.

## Timing boundaries
The primary metric is **speech end → Android output**; it includes the end-of-speech pause. Trigger → Android output also includes the question and recorder handoff. Trigger means local wakeword detection, manual native-session start, or confirmed Always on activity, not the acoustic onset of the wakeword.

The timeline records native Assist start, WebSocket connection/authentication, HA pipeline events as received on the tablet, microphone start, local activity/end frames, upload markers, job submission/acceptance/receipt, HTTP first byte, decoded PCM, initial buffer, route confirmation, first submitted PCM, playback progress and completion.

Local activity uses the existing 20-ms energy detector, not semantic voice recognition. Server stages are tablet-observed intervals including transport/scheduling, not isolated GPU compute time. TTS completion supplies an audio URL; synthesis can continue while streamed audio is downloaded. Intervals can overlap and must not be added together. Missing measurements display as a dash.

Streaming output is observed when AudioTrack playback-head progress crosses the first response frames after silent route verification. The file fallback observes MediaPlayer position advancing after unmute using its existing 100-ms route timer. OUTPUT_QUALITY identifies this distinction. Neither observation determines extra acoustic Bluetooth/Echo latency or leading silence in generated audio.

The exact playback job ID correlates the response. Events that occur before submit's HTTP response retain their original tablet timestamp. Other announcements are not counted as the reply. The existing 650-ms job status polling is not used to estimate playback start.

## Comparisons
Use the same question, route and pause configuration. Export a cold run separately, clear history, then collect roughly 10–20 warm runs. Statistics separate trigger kind, output, player and pause configuration. P50/P95 only include successful runs with observed playback progress and show sample count n. Failed and interrupted requests remain visible.

## Storage
Only the last 20 requests and up to 32 internal playback observations are retained. Export includes relative times, trigger/outcome and bounded technical counters. No audio, transcripts, answers, addresses, credentials or HA job IDs are exported. Turning recording off interrupts the measurement, not the conversation. Clearing history retires in-flight callbacks.

All times use the tablet monotonic clock. No new diagnostic network requests, audio waits or per-frame disk writes are added. Metadata checkpoints are coalesced outside the audio thread. The GPU Worker needs no changes.

[Assist events](https://contributors.home-assistant.io/core/internals/assist-pipelines/) · [AudioTrack playback head](https://developer.android.com/reference/android/media/AudioTrack#getPlaybackHeadPosition())

Emulator screenshots use synthetic test metadata, not measurements from your tablet.

## Comparing 1.2.7 and later
After JOB_ACCEPTED the native session sends one wakeup request (PLAYER_WAKEUP) to the running player. Its existing network executor immediately checks the HA queue. While output is busy, completion triggers the next check. A wakeup is not confirmation of playback and cannot reconnect a stopped player. The 900-ms fallback poll remains for external HA jobs and recovery.

BUILD_CODE identifies each newly recorded run. Statistics keep builds separate from legacy history without build metadata. Compare the same trigger, output, player and pause. To test shorter endpointing, a tablet can be set from 1700 to 1100 ms; increase this if questions get cut off. Always on honors the same setting. The app update does not globally shorten defaults or saved preferences.

The startup buffer setting is audio duration, not a fixed delay: 600 ms of audio may fill much faster. Neither that setting nor a single sample establishes a guaranteed latency gain.
