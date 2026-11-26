# TAFA: one speech path, one management UI

**TAFA App 0.3.39 / HA integration 0.4.23 / Device Bridge 1.0.3**

## Architecture

Android wakeword → native tablet microphone → **Home Assistant Assist** pipeline **TAFA Lokal** (Whisper/Wyoming, Ollama, TTS) → authenticated TAFA room audio → native tablet playback to the paired **Bluetooth speaker**. There is no browser microphone mode or competing conversation transport. Qwen and Piper are alternative backend *voices*, not alternate tablet audio paths.

TAFA no longer creates an extra dashboard sidebar panel. Manage voice and devices under **Home Assistant → Apps → TAFA → User interface**. Existing personal dashboards, automations and Assist pipelines are preserved.

## Setup

1. Update the TAFA App. Restart Home Assistant Core after installing the updated integration. The installer intentionally does not overwrite an externally managed integration.
2. In TAFA → **Settings**, configure the speech server, Wyoming STT, and an Ollama conversation agent. Verify that the **TAFA Lokal** Assist pipeline works.
3. Install **TAFA Device Bridge 1.0.3** on each tablet; sign in to HA securely, grant microphone access, and start native playback and wakeword recognition.
4. Pair the desired Echo/Bluetooth speaker using **Android Bluetooth settings**, then verify ordinary media playback.
5. Visit TAFA → **Devices & multiroom**. Each running tablet enrolls using its own stable device ID; control its wakeword, mute, mic parameters and status in HA.
6. Under **Devices & multiroom → Create new room** first create a room using a dedicated non-admin HA user, **even without an enrolled tablet**. Sign Device Bridge into the **test server** using this user token, start wakeword recognition to enroll the tablet, then pair it with the already created room. Transfers from other users require an explicit confirmation. No fixed four-device cap.

## Entities per tablet

HA dynamically exposes sensors for connectivity, wakeword, microphone, playback, Bluetooth, battery, app version, last contact and last wakeword; switches for microphone mute and optional display dimming; numeric controls for wakeword confirmation, cooldown, handoff, speech pause, digital input gain and brightness; and a wakeword selector.

The Android app re-fetches HA-owned settings periodically. On HA connectivity loss the wakeword service fails closed to avoid ignoring remote mute.

**Follow-ups have no numeric limit**. They continue after successful spoken responses, until a no-answer turn, mute or stop.

## Display limitations

Optional Android **Modify system settings** permission allows global brightness adjustments after explicit consent and TAFA enablement. It does **not** reliably turn off, unlock, or wake a sleeping screen without privileged Android device-management rights. Adaptive brightness and manufacturer power policies may interfere.

## Compatibility and privacy

Device settings are stored in authenticated HA storage, not hardcoded tablet slots. Diagnostic sensors never persist audio or transcripts. Updating an installed release APK requires the **same Android signing key**; a CI debug APK is not a drop-in replacement. Existing automations and dashboards are intentionally left untouched.
