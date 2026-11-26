# Historical Jarvis Multiroom documentation (not for fresh TAFA installations)

**Current guide:** [TAFA Multiroom](../MULTIROOM.md).

# Jarvis Multiroom — HA backend 1.7.0 / Android 0.6.0

**English** | [Deutsch](MULTIROOM.de.md) · [Project](../../README.md)

One Home Assistant, multiple tablets and Bluetooth speakers, separate room audio queues and optional camera/motion entities. One central CPU speech server and optional GPU Worker 2.2.0 remain sufficient. Legacy single-device mode is still supported. One physical tablet has passed room audio, camera and dashboard playback tests; synthetic two-room HTTP/entity and routing tests are included. Concurrent physical two-tablet testing and a clean installation remain outstanding.

## 1. Install the backend and cards

- Back up HA. Update the entire [Jarvis Tablet Audio integration](../custom_components/jarvis_tablet_audio/) to 1.7.0 in `/config/custom_components/jarvis_tablet_audio/`, preserving configuration. Check HA configuration and restart. For a new system, first follow the [base HA setup](../../docs/en/home-assistant.md) and [CPU speech setup](../../docs/en/proxmox.md). The Marketplace base integration alone does not install this separate backend.
- Copy `jarvis-room-admin-v0.2.0.js` and `jarvis-room-assist-v0.1.1.js` from [homeassistant/www/jarvis](../www/jarvis/) to `/config/www/jarvis/`. In Settings → Dashboards → Resources (advanced mode if needed), register `/local/jarvis/jarvis-room-admin-v0.2.0.js` and `/local/jarvis/jarvis-room-assist-v0.1.1.js` as JavaScript modules. Replace older URLs of the same cards, then reload the frontend.
- Configure an Assist pipeline with STT, conversation agent and Jarvis streaming TTS (e.g. `tts.jarvis_tablet_stream`). For optional wake word, configure a second pipeline with a compatible wake-word engine. Find your actual pipeline IDs in HA or via its Assist pipeline list API.

## 2. Create one room account per tablet

1. Settings → People → Users: create a dedicated active **non-admin** account for each tablet, e.g. Jarvis Living Room. Use a unique strong password. Prefer local-only access with trusted local HTTPS. If using an external HTTPS hostname and local-only blocks login, deliberately decide whether to allow external access; never grant admin privileges just for Multiroom.
2. Create an admin-only dashboard and add this manual card:

   ```yaml
   type: custom:jarvis-room-admin
   ```
3. Enter a room slug (e.g. `living_room`), select its user, Add room. HA creates a device, camera and motion entity. Assign the device to the corresponding HA Area under Settings → Devices & services → Devices. Copy the device ID from the device page URL to the optional HA device ID field in the admin card and save. This passes area context to Assist. Optionally set both quiet-hour times.
4. Repeat for each tablet. Do not share accounts or tokens across rooms. Routing uses the authenticated HA account, not a client-supplied room name. Normal HA entity permissions still apply; non-admin is not complete entity-level isolation.

## 3. Configure Android

Install the [signed 0.6.0 APK](../../android/downloads/HA-Jarvis-Echo-Relay-0.6.0-preview.apk) over the previous version. Pair the local Echo using Android Bluetooth settings and test media audio. Log into HA as the room user; create a long-lived token under Profile → Security and scan its one-time QR code or enter the token privately in Relay. Enter the HA base address, enable **Room audio (experimental)** and start/restart the player to save the setting.

App and dashboard must use the **same room account**. Prefer trusted HTTPS. The app may use a numeric local HTTP address with explicit consent (credentials and media travel unencrypted); the browser/WebView microphone still needs trusted HTTPS and microphone permission. Local HTTP does not work for dashboard microphone capture. No router changes are required if existing HTTPS works. Never place tokens in Git or dashboard YAML.

**Optional offline setup:** [Local HTTPS / split DNS](../../docs/en/local-https.md) uses an existing NGINX/Certbot proxy and the same trusted hostname inside the LAN. No second HA proxy is needed; local HTTP cannot supply a trusted WebView microphone origin.

## 4. Create a room assistant dashboard

Create a normal dashboard (not admin-only) and add a manual card:

```yaml
type: custom:jarvis-room-assist-card
title: Jarvis · Room assistant
pipeline_id: YOUR_JARVIS_PIPELINE_ID
# Optional: wake_pipeline_id: YOUR_WAKEWORD_PIPELINE_ID
instance_id: living_room
```

Use a distinct instance ID per room. Login as its dedicated user on the tablet; open the room card. It should display the room name and Echo Relay connected. Use the card's microphone/one-shot control, not HA's native header Assist. Grant microphone permission, start explicitly and ask a short question; check speech on the room's Bluetooth Echo. The HA device ID provides area context if the pipeline/agent supports it. No fallback to another room, no global audio helpers.

Existing custom dashboards need an explicit transport migration. The optional [generic kiosk audio adapter](../www/jarvis/jarvis-kiosk-room-audio-v0.1.0.js) is for compatible custom Voice controllers only; standard installations should use the standalone card. The private kiosk layout and configuration are not distributed.

## 5. Optional camera and motion

Permission is off by default. Only enable in shared rooms with informed consent from everyone present, never private rooms. Enable camera permission in the admin card, save, then explicitly start the selected camera on the tablet. Stop locally or via its visible notification. Revoking HA permission clears the stored frame and rejects uploads. Set 1/2/3/5/10-second refresh; actual rate depends on capture/upload. Separate refreshed JPEGs, not full-rate video. Images expire after 15 seconds in RAM, no archive. Optional coarse image motion is local, not identity recognition or cross-room tracking. Explicit tablet vision queries from a room account use its own camera without legacy fallback. HA camera permissions still apply. Android 0.6.0 may show the old admin-token error if permission is denied; check permission and account, **do not use an admin token**.

## 6. Announcements

In HA Developer Tools → Actions or an automation:

```yaml
action: jarvis_tablet_audio.room_audio
data:
  action: announce
  rooms:
    - living_room
    - office
  message: "Dinner is ready."
response_variable: result
```

Use `room: living_room` instead for one room. The admin card also sends to selected rooms. Automatic announcements respect quiet hours and reported activity; accepted means queued, not confirmed playback. Optional [disabled greeting example](multiroom-greeting.example.yaml) uses a local motion sensor, no camera or identification. Configure placeholders and daily guard; day is marked on acceptance. Existing legacy automations are not automatically migrated.

## Troubleshooting

| Symptom | Check |
|---|---|
| App connected, card not ready | Same user in both; new room card/resource, reload cache; read status/HTTP error. |
| Microphone error | Trusted HTTPS, microphone permission, stop competing microphone sessions. |
| Camera denied / admin-token error | Enable room permission, correct account, restart locally. |
| No speech | Bluetooth media route, running app, streaming TTS, targeted test announcement. |
| Wrong room for commands | HA Area, device ID and agent support. |
| Move tablet | Stop camera/player, revoke old mapping, configure new room and account, update Area and card instance. |

Before relying on multiple tablets, test independent responses, concurrent requests, offline/busy without cross-room fallback, each camera/stop control and quiet hours. [Android setup](../../android/README.md) · [Security](../../docs/en/security.md).

## Personalized office greeting (backend 1.7.1)

The legacy `proactive` action only inspected the old single-device camera. Backend 1.7.1 adds an optional `room: buero` argument to administrator `jarvis_tablet_audio.proactive` calls with `action: check`, using fresh opted-in room-camera frames. The emitted `jarvis_echo_relay_detection` event includes `room` and `camera_entity_id`.

On existing installations update `relay_proactive.py` and `relay_camera.py` from `homeassistant/custom_components/jarvis_tablet_audio/` in the HA custom integration directory, then reload the integration or restart HA. The room parameter is **not available until the updated backend is installed**. Leave backend `greeting` disabled when an HA room automation handles announcements.

Configure `automation.jarvis_tablet_bewegung_mit_vision` to trigger on `binary_sensor.jarvis_tablet_buero_bildbewegung` and pass both `action: check` and `room: buero` to the `jarvis_tablet_audio.proactive` service. Then disable generic `automation.jarvis_morgendliche_begrussung_buro_multiroom` and enable prepared event-driven `automation.jarvis_buro_personalisierte_begrussung_multiroom`.

Names are read from `input_text.jarvis_name_mann`, `input_text.jarvis_name_frau`, and `input_text.jarvis_name_kind`. Visual appearance categories are estimates, **not reliable person identification**. Only a clear single-person estimate includes a configured name; all other cases use a neutral greeting. Do not use them for authentication or sensitive decisions. Camera capture requires informed consent.

### TAFA kiosk: room audio for an account later granted admin permissions

The standalone Jarvis room card already uses the correct room transport. A separately integrated TAFA kiosk may incorrectly switch to the legacy audio helper based on `is_admin`. That helper can remain at `idle`, although the **assigned room player is online and ready**.

Custom kiosks can use the [reusable room detection helper](../www/jarvis/tafa-room-routing-v0.1.0.mjs). It queries the **authenticated** HA user with `POST /api/jarvis_echo_relay/room_audio` (`action: status`). A room transport is selected only when a room assignment exists; otherwise the legacy audio route remains unchanged. After creating the `Voice` instance in `ensureVoice(card)`, **before** the existing `if(v.roomMode&&!v._roomAttached)` check:

```js
const v = card._jarvisIntegratedVoice;
if (!v.roomMode && !v._tafaRoomProbeStarted) {
  import(new URL("/local/jarvis/tafa-room-routing-v0.1.0.mjs", location.origin).href)
    .then(m => m.maybeEnableProvisionedRoomAudio(card, v, ensureVoice))
    .catch(error => console.warn("TAFA room routing:", error));
}
// Keep existing if(v.roomMode&&!v._roomAttached) logic unchanged.
```

Copy this module from the repository to `/config/www/jarvis/`. The private TAFA home dashboard source is not published; merely adding this module will not change a dashboard without integrating it. Continue provisioning **dedicated non-admin users** for new rooms. No room assignments, existing room playback, or other rooms are modified. Test: `node --test tests/test_tafa_room_routing.mjs`.
