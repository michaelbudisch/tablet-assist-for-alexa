# Echo Relay Assist dashboard (v1.2.0)

> **Multiroom from Android 0.6.0 / HA 1.7.0:** [New room setup](../../homeassistant/examples/MULTIROOM.md). The following guide is for legacy single-device mode with global helpers.

**English** | [Deutsch](../echo-relay-dashboard.md) · [Project overview](../../README.md)

> **Optional current preview:** [Native HA automations and family settings](ha-automations.md). This page describes the original card 1.2.0 and its settings. Optional card 1.3.0 uses family helpers and the reusable speech action instead.

## Setup

1. Install Echo Relay on Android, pair the Echo using system Bluetooth settings, connect the app to HA and start its player.
2. Create two Text helpers (maximum 255 characters): `input_text.jarvis_native_audio_command` and `input_text.jarvis_native_audio_status`. Reuse existing helpers, or use the optional [YAML template](../../homeassistant/templates/echo-relay-helpers.yaml) in a configured packages directory. Do not define them twice.
3. Copy the five files `echo-relay-assist-card-v1.2.0.js`, `jarvis-settings-v1.1.0.js`, `jarvis-model-settings-v1.1.0.js`, `jarvis-camera-preview-v1.2.0.js` and `jarvis-proactive-v1.0.0.js` from [homeassistant/www/jarvis](../../homeassistant/www/jarvis/) into `/config/www/jarvis/`. Register only `/local/jarvis/echo-relay-assist-card-v1.2.0.js?v=1.2.0` as a Dashboard Resource of type JavaScript module.
4. Use your preferred HA Assist pipeline, or set your own pipeline IDs below. Wake-word mode needs a configured server-side wake-word engine. Continuous and one-shot modes do not require it. Use HTTPS and grant microphone access.
5. Tap the microphone: green wake word → blue continuous → off. It stops when hidden or disconnected. Recording starts manually after a reload; an explicitly enabled proactive follow-up may also briefly open the microphone after a greeting. Capture pauses during playback and reopens for the next turn in continuous mode. Inform people nearby.
6. Settings contain Echo Relay (default), browser/tablet playback and explicit native Assist fallback. The main button always controls the dashboard assistant. Disable concurrent Companion App wake-word detection, or configure the optional `native_notify_service`. Use only one active controller per app/helper pair. Android app 0.3.0 streams MP3/PCM WAV with a small startup buffer; 0.2.0 still downloads the whole file. The card does not update the APK.

```yaml
type: custom:echo-relay-assist-card
title: Echo Relay
# Optional:
# pipeline_id: YOUR_ASSIST_PIPELINE_ID
# wake_pipeline_id: YOUR_WAKEWORD_PIPELINE_ID
# native_notify_service: mobile_app_your_tablet
# status_entity: input_text.your_optional_debug_status
# output: native_audio
```

The command/status entity names default to the app's fixed helper IDs. Only override `command_entity` and `relay_status_entity` if your Android client is configured to use the same pair. Optional direct Alexa fallback: configure both `alexa_script: your_script_service_name` (no script prefix) and `alexa_notify: notify.your_echo`. The script must accept `text` and `lautsprecher` fields. Direct Alexa may send audio via the Amazon cloud. Never use it for confidential replies. The browser card never stores HA access tokens; it uses the active authenticated HA connection.

## Motion-triggered actions

The feature is opt-in and requires backend 1.6.0, GPU Worker 1.9.0 and all five frontend modules. Install the native motion automation once. **Test mode repeats at any time**, subject to the configured cooldown; normal mode uses the morning window, a minimum five-minute cooldown and at most one action per local day. No computer wake-up, scheduled polling or continuous vision inference. The worker returns a fixed validated schema for people, dogs and coarse adult/child/unknown appearance; uncertain or invalid results trigger nothing. No identity or face comparison; the updated worker optionally returns coarse apparent presentation categories, not actual gender.

Optional fixed greeting names are configuration and apply to every matching category. Rain advice comes from an actual HA forecast. A visible idle authenticated dashboard claims a single native Echo Relay stream, waits for playback confirmation and optionally listens for a yes/no follow-up. Ordinary questions take precedence over new proactive checks. A manually selected HA script receives `jarvis_detection`; other automations can listen for `jarvis_echo_relay_detection` with `labels`, `camera_entity_id`, `detection` and `test_mode`. No image is included in events. Script execution marks the daily guard; greetings mark it only after confirmed tablet playback. One shared cooldown limits checks; restart resets the in-memory cooldown but retains settings and the daily action date.

Administrative API: `jarvis_tablet_audio.proactive`, `action: get` returns a revision and status; `action: set` requires that revision and the complete `settings` dictionary. `action: check` is available to HA automations or administrators. `heartbeat`, `claim` and `ack` are used by authorized dashboard clients. Worker `/detect` accepts only bounded images and allowlisted model/residency/context values. Existing camera questions and view-only commands remain separate from this explicitly enabled automatic feature.

Copy the card and all five modules listed in Setup, install the backend update, restart HA and fully reload the dashboard. In **Jarvis → Proactive actions**, an administrator can opt in to motion analysis; new installations leave it off. Install the [native motion automation](../../homeassistant/templates/echo-relay-proactive-automation.yaml) and select the correct motion entity. The service enforces its own guards; it does not run a continuous loop. Default cooldown is 60 seconds, selectable from 30 seconds to 30 minutes. An equal start/end time means all day. A fixed greeting and HA weather entity are optional. The selected name is not a personal identification. The dashboard can offer a daily overview and interpret an affirmative or negative follow-up. The private kiosk uses its daily overview; the public card sends the question to the configured Assist pipeline. No personal calendar is created.

**Check now and run actions** uses the current image without requiring a motion signal. Opt-in and cooldown still apply; it may speak or start the configured script. A visible, idle dashboard with Echo Relay ready is required for a greeting. Passive wake-word listening or at least two seconds of silence in continuous mode may be briefly paused; the prior listening mode is retained. No image archive is created.

## Settings

| Section | Settings | Storage |
|---|---|---|
| Voice & audio | Output, fallback, speech pause, sensitivity, follow-ups, conversation window | Per browser and card instance |
| Display & cameras | Captions, display duration, camera infobox duration | Per browser and card instance |
| AI & performance | Text/vision models, residency, context, loaded models | Shared HA settings, administrator only |
| Proactive actions | Opt-in, test mode, cooldown, greeting, weather and HA actions | Shared HA settings |
| History & diagnostics | Session history, test, replay, fallback, reset browser settings | History in memory only |

Model and helper choices use inline radio controls instead of dropdown overlays. Live state updates preserve control nodes and pending selections; failed helper saves restore the confirmed value and display a local error. Tabs support arrow keys, Home and End. Colours follow the active HA theme. Browser changes are immediate; shared model changes require **Save for Jarvis**. Resetting browser defaults never changes shared models.

The [portable Lovelace example](../../homeassistant/templates/echo-relay-dashboard.yaml) works without the private kiosk. The optional `jarvis-control-panel` 1.6.0 also needs the legacy package helpers/scripts and configured room entities. It groups voices/system, announcements, notifications/rooms and timers/tablet. Copy the complete staged output when installing from scratch. Replace the old controller resource entry; loading two versions of one custom element does not upgrade an already registered element. Update to Jarvis Tablet Audio 1.6.0 and GPU Worker 1.9.0, restart HA once, then reload the dashboard.

Additional kiosk-only controls appear when the host supports their features: home-data cards, navigation/return to private home views and Wikipedia presentation. The standalone card exposes its working audio, conversation, captions, history, camera and AI preferences. Android camera sharing remains configured in the app. The separate Marketplace sidebar is not replaced by this Lovelace resource update.

Follow-up modes use the configured conversation window. "On questions" opens the microphone after a question in the answer or an Assist follow-up; "Only on Assist request" follows `continue_conversation`. The kiosk's intelligent mode also considers its knowledge context. Speech pause and sensitivity apply on the next recording; camera closing time applies on the next infobox.

Independent of the private Hauszentrale dashboard. Works with a Home Assistant dashboard and the Android Echo Relay command/status helper protocol. No changes to the APK. Browser tests cover German/English settings, theme/layout changes, delayed HA acknowledgements, model saves and the camera lifecycle. Physical microphones, Echo devices and Android WebViews still require testing on your own hardware.

## Camera questions

With Jarvis Tablet Audio 1.5.0 and GPU Worker 1.8.0, configured door/outdoor/tablet camera questions open the corresponding Jarvis camera infobox only on the requesting visible dashboard. Jarvis describes a snapshot, including generic visible people, clothing and carried objects, without identity recognition. The dialog automatically starts a muted live view; the description remains a single-image observation and may be wrong. Other devices, hidden dashboards and native Companion Assist do not automatically open this dialog. Ordinary door controls retain their existing route. A failed preview never interrupts the spoken response.

App **0.5.0** continues to work; no APK update is required. Copy all five JavaScript files, update the card resource, restart HA after the backend update, then reload the dashboard. This also applies to the separately maintained Hauszentrale Kiosk controller when its preview hook is installed.

## Routing fix (HA integration 1.4.2)

For Jarvis router pipelines disable “Prefer handling commands locally”. The router handles explicit camera questions first and still delegates ordinary device commands to native HA before using an LLM. Other pipelines need no change. Integration 1.4.2 adds an administrator-only `jarvis_tablet_audio.camera_pipeline_check` diagnostic accepting camera questions only; it runs the real configured intent pipeline without microphone capture, TTS or playback. Inspect `speech`, `processed_locally`, `prefer_local_intents` and `errors`. A camera answer should reach Jarvis (`processed_locally: false`). No Android update is required.

## Live view and front camera (1.4.3)

The configured outdoor camera now answers “Vorderkamera” and “Vorderseite” visual questions. The live preview uses Home Assistant's standard picture-entity card in live mode with muted playback. It reuses the kiosk infobox delay (30 seconds by default after speech) or standalone `camera_info_seconds`, supports one 60-second extension and always closes within three minutes. Closing, a new question, hiding or removing the dashboard disposes the player. Description text still concerns a snapshot. Copy the new versioned JavaScript files and reload the dashboard; update the HA integration to 1.4.3 and restart HA for the new aliases. No APK or worker update is needed.

## View or describe (1.4.4)

View-only commands bypass the dashboard Assist/TTS pipeline entirely and never call the vision worker. Bare camera aliases also show the feed. Explicit visual questions (or an explicit “describe” request) still infer a snapshot and speak its description. “Zeige Kameras” opens up to three authorized configured feeds in one responsive grid; closing the infobox removes every player. Native Companion Assist cannot open this dashboard-local view and returns a short dashboard hint, without inference. Update backend 1.4.4, the versioned module and controller, then restart HA and reload the dashboard. No APK or GPU-worker update is required.

## AI models and performance (1.5.0)

An HA administrator can open **AI & performance** (worker 1.8.0 or newer). Select the same Qwen3-VL 4B Instruct model for both text and images or use Qwen3 4B Instruct for text and Qwen3-VL 4B Instruct for images separately. Select residency (0/60/120/300/600 seconds) and context (2048/4096/8192 tokens). Higher context consumes more VRAM. Opening the panel does not load models. Save changes centrally with **Save for Jarvis** when Jarvis is idle; refresh the status to read actual state.

Copy [jarvis-model-settings-v1.1.0.js](../../homeassistant/www/jarvis/jarvis-model-settings-v1.1.0.js) alongside the controller into `/config/www/jarvis/` (no separate resource entry). Controller 1.1.0 dynamically mounts the shared settings. Also copy jarvis-settings-v1.1.0.js into the same directory. Use backend 1.5.0 and worker 1.8.0, restart HA once after installing backend code and reload the dashboard. Settings are server-backed, not browser-local. Model changes do not restart the tablet camera. Only installed allowlisted models are offered; no automatic downloads. Shared text/vision uses the same model tag, context and residency; keep Ollama's existing one-model limit. Speech recognition and synthesis still use their existing services. No APK update is required.

For automation-free administration, `jarvis_tablet_audio.model_settings` with `action: get` returns a revision. `action: set` takes that revision plus `text_model`, `vision_model`, `keep_alive` and `num_ctx`. Non-admin requests and stale or unsupported settings are rejected. The service never returns worker credentials or system prompts.

## Changes

- v1.1.0: shared theme-aware settings with four keyboard-accessible tabs; inline model and central helper choices; portable microphone, conversation, caption, history and fallback preferences. Optional control panel 1.6.0 groups house functions and preserves choices while HA acknowledges changes.

- v1.0.5: administrator model selection, shared residency/context and loaded-model status.

- v1.0.4: silent view-only camera commands and an authorized camera overview; explicit visual questions retain snapshot descriptions.

- v1.0.3: auto-started muted live camera infobox, speech-end countdown, stream cleanup and one-time extension.

- v1.0.2: configured camera preview for camera questions, restricted to the active requesting dashboard; shared backend mapping and read permissions.

- v1.0.1: wake-word and speech detection, processing/buffering and playback indicators (DE/EN). Speech detection indicates voiced audio, not speaker identity.

- v1.0.0: microphone cycle, explicit foreground capture, native Echo Relay status/command handling, settings and optional fallbacks. No private IDs or dependencies on Hauszentrale; English/German settings and main state labels. Detailed backend error text may be German or supplied by HA.
