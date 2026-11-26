# Archive – older Jarvis camera guide

**Current:** [TAFA camera setup](../camera-preparation.md). Not for new installations.

# Tablet camera with TAFA – TAFA Device Bridge 1.0.6 + HA integration 0.4.24

**Current clean-install path:** The camera receiver is included in the unified TAFA Home Assistant integration. **Do not install a separate Jarvis Tablet Audio receiver.** Historical Jarvis steps below are archived for older systems only.

1. On the **selected test server**, update TAFA App to **0.3.40**, including HA integration **0.4.24**, then restart HA Core once for the updated Python integration.
2. Open **Apps → TAFA → User interface → Devices & multiroom → Tablet cameras per room**. Explicitly select **On** for the chosen room, e.g. `buero`, and save. Camera uploads default to **Off**.
3. Use **TAFA Device Bridge 1.0.6** and the **non-admin room user's** HA token for that server. No admin token needed. In the Android camera settings, choose the lens, grant camera permission and explicitly tap **Start camera for HA**. This service is independent of voice/audio.
4. HA exposes a room camera and motion sensor under the TAFA integration. Images use authenticated `/api/tablet_assist_for_alexa/room_camera/register` and `/frame`; never the legacy `/api/jarvis_echo_relay` route.
5. Stop the stream in Android or disable the room's camera permission in TAFA. Disabling also clears cached frames.

Only user-started snapshots are sent; no persistent recording or offline queue. Frames are kept in RAM and expire when stale. Consider the privacy of anyone in view. **404:** TAFA camera API is missing on the selected HA server. **403:** room user, ownership or camera permission missing. **409:** another active tablet camera session.

---

## Archived Jarvis camera documentation (not for clean TAFA installations)

# Camera and local vision · 0.5.0

**English** | [Deutsch](camera-preparation.de.md) · [Project overview](../../README.md)

## Setup

1. HA needs the **Jarvis Tablet Audio 1.5.0** camera receiver from `homeassistant/custom_components/`. Preserve `const.py`, credentials and custom dialogue/search extensions on existing installations; integrate the camera modules into setup and routing. Python updates require an HA restart. New portable installations use `homeassistant/install.py`.
2. In **Settings → Devices & services → Jarvis Tablet Audio → Configure**, select outdoor and door cameras. A blank vision address uses the existing GPU host on port 10503; alternatively provide a local IP and port without a path. The existing Qwen/worker key is used. GPU Worker 1.8.0 needs the vision profile and an installed vision model. No additional production Docker service is required on the Android side.
3. Store the HA address/token in the app, open the camera settings, choose front/rear camera, optionally enable the image-motion sensor and explicitly start the HA camera. Pairing requires an HA administrator token; the audio player need not be running. Enable capture only with informed consent from affected people.
4. The default entities are `camera.echo_relay_tablet` and `binary_sensor.echo_relay_bildbewegung`. If names differ, use the integration's entities. The vision action locates the tablet camera by its unique ID.
5. The shipped grammar is German. Try "Was ist draußen los?", "Wer ist an der Haustür?", "Was ist an der Haustür?", "Was sieht die Haustürkamera?", "Was siehst du?" or "Was halte ich in der Hand?". Alternatively call `jarvis_tablet_audio.describe_camera` with `source: outside`, `door` or `tablet` and `mode: scene`, `objects` or `object_in_hand`; the response contains `description`. Other conversations and home commands retain their normal routing.

## Camera infobox and door questions

Camera questions such as “Who is at the front door?” also open the configured camera in the requesting visible dashboard with card 1.0.3 and the shared preview module. Other dashboards and native Companion Assist do not open automatically. Visible people can be described generically without names or face matching. The existing 0.5.0 APK remains compatible; reload the updated dashboard.

The updated controller (card 1.0.4 with `jarvis-camera-preview-v1.2.0.js`) displays the configured camera while describing a snapshot. Generic visible clothing and carried objects may be described; the model never identifies or matches faces. Door-control and door-status commands remain ordinary home commands.

## Operation and limitations

Use the matching HA receiver and existing GPU Worker vision service. Explicitly start camera delivery in app settings. Its dedicated foreground notification stops it independently of audio. Images are pushed roughly every two seconds using the saved HA origin and administrator token. No tablet image server, disk recording, automatic boot start or offline queue is created. Stop invalidates the session; images expire after 15 seconds without delivery. Select outdoor/door cameras in the integration options. `describe_camera` returns a description for tablet/outdoor/door images on explicit request.

The camera has its own foreground-service notification and is independent of audio/keepalive. The local camera test closes its preview when exited. HTTPS uses normal certificate validation and authentication without redirects. Explicitly approved local HTTP is unencrypted. To change the paired device, stop the old camera and call `jarvis_tablet_audio.unpair_camera` as administrator. Stop clears the image and invalidates the session; `jarvis_tablet_audio.camera_vision_status` checks the worker and mapping without transferring an image.

Motion compares coarse pixel changes and suppresses uniform brightness changes; it is not object detection and can miss motion or react to light. The worker describes still images, not full-rate video. External cameras may provide an older snapshot, and descriptions can be wrong. Model changes and capture can delay responses. Android battery management and screen-off behaviour need real-device testing.

## Protocol and validation

- Authenticated `POST /api/jarvis_echo_relay/register` pairs a stable 32-hex device ID and returns an ephemeral session.
- `POST /api/jarvis_echo_relay/frame` accepts JPEGs up to 2 MiB with session/device, increasing sequence, capture time and optional motion headers. Normalization strips metadata; only the latest image is retained. Old sessions/frames are rejected.
- `DELETE /api/jarvis_echo_relay/frame` stops the remote session and clears the image.
- Native Android tests use emulated cameras and a private HTTP receiver to verify background JPEG delivery, authentication, sequence/motion metadata and remote Stop.
- `tests/relay_camera_e2e/run.sh` tests pairing, camera/motion entities, authorization, options/reload, spoken routing and stale/late frames in isolated real HA with synthetic image/model fixtures. Publication waits for this check and Android checks.

![Camera screen with emulated scene](ui-camera-tablet.png)

## Routing fix (HA integration 1.4.2)

For Jarvis router pipelines disable “Prefer handling commands locally”. The router handles explicit camera questions first and still delegates ordinary device commands to native HA before using an LLM. Other pipelines need no change. Integration 1.4.2 adds an administrator-only `jarvis_tablet_audio.camera_pipeline_check` diagnostic accepting camera questions only; it runs the real configured intent pipeline without microphone capture, TTS or playback. Inspect `speech`, `processed_locally`, `prefer_local_intents` and `errors`. A camera answer should reach Jarvis (`processed_locally: false`). No Android update is required.

## Live view and front camera (1.4.3)

The configured outdoor camera now answers “Vorderkamera” and “Vorderseite” visual questions. The live preview uses Home Assistant's standard picture-entity card in live mode with muted playback. It reuses the kiosk infobox delay (30 seconds by default after speech) or standalone `camera_info_seconds`, supports one 60-second extension and always closes within three minutes. Closing, a new question, hiding or removing the dashboard disposes the player. Description text still concerns a snapshot. Copy the new versioned JavaScript files and reload the dashboard; update the HA integration to 1.4.3 and restart HA for the new aliases. No APK or worker update is needed.

## View or describe (1.4.4)

The shipped German grammar separates view-only aliases from explicit visual questions. Door aliases include "Zeige Haustürkamera", "Haustür" and "Klingel". Outdoor aliases include "Zeige Vorderseite", "Vorderkamera" and "Zeig mir die Außenkamera". "Zeige Kameras" opens the authorized camera overview; a tablet image must be fresh. "Wer ist an der Haustür?" and "Was ist draußen los?" request a snapshot description with the corresponding feed. Ordinary door actions and definitions do not request image analysis.

View-only commands bypass the dashboard Assist/TTS pipeline entirely and never call the vision worker. Bare camera aliases also show the feed. Explicit visual questions (or an explicit “describe” request) still infer a snapshot and speak its description. “Zeige Kameras” opens up to three authorized configured feeds in one responsive grid; closing the infobox removes every player. Native Companion Assist cannot open this dashboard-local view and returns a short dashboard hint, without inference. Update backend 1.4.4, the versioned module and controller, then restart HA and reload the dashboard. No APK or GPU-worker update is required.

## AI models and performance (1.5.0)

In Jarvis settings, open **AI models and performance** as an HA administrator with GPU Worker 1.8.0. The panel shows installed text/vision models, loaded models and Ollama GPU memory. Opening it does not load a model. Choose Qwen3-VL 4B Instruct for both or Qwen3 4B Instruct for text and Qwen3-VL 4B Instruct for images. Set residency (0/60/120/300/600 seconds) and context (2048/4096/8192 tokens); higher context uses more VRAM. Save centrally when Jarvis is idle; refresh status to read the actual state.

Copy [jarvis-model-settings-v1.0.0.js](../../homeassistant/www/jarvis/jarvis-model-settings-v1.0.0.js) alongside the controller into `/config/www/jarvis/` (no separate resource entry). Controller 1.0.5 dynamically mounts the panel. Use backend 1.5.0 and worker 1.8.0, restart HA once after installing backend code and reload the dashboard. Settings are server-backed, not browser-local. Model changes do not restart the tablet camera. Only installed allowlisted models are offered; no automatic downloads. Shared text/vision uses the same model tag, context and residency; keep Ollama's existing one-model limit. Speech recognition and synthesis still use their existing services. No APK update is required.

For automation-free administration, `jarvis_tablet_audio.model_settings` with `action: get` returns a revision. `action: set` takes that revision plus `text_model`, `vision_model`, `keep_alive` and `num_ctx`. Non-admin requests and stale or unsupported settings are rejected. The service never returns worker credentials or system prompts.
