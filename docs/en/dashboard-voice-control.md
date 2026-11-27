# Control TAFA voice from your own Home Assistant dashboard

[Deutsch](../dashboard-voice-control.md) · [Native voice path](native-only.md) · [TAFA App](app.md) · [Developer: response cards](dashboard-integration.md)

A Home Assistant dashboard can manage an enrolled TAFA Device Bridge microphone even while the Android app or dashboard is in the background. This developer page documents the supported controls without cluttering the project's main README.

## Recommended: use the Home Assistant entities

For each enrolled tablet, find its entities under **Settings → Devices & services → TAFA → Devices → tablet**:

| Entity type | Purpose | Action |
| --- | --- | --- |
| `switch.…_mikrofon_stumm` | Native microphone mute | `switch.turn_on` mutes; `switch.turn_off` enables |
| `select.…_nativer_sprachmodus` | Native voice trigger | `Rufwort` (wake word) or `Immer an` (always on) |
| `select.…_anschlussfragen_ha_grenze` | Follow-up ceiling | `Aus` (off), count, or `App-Einstellung` (app setting) |

**Entity IDs differ per installation.** Copy the real IDs from HA instead of pasting these placeholders unchanged:

```yaml
type: entities
title: TAFA – voice control
entities:
  - entity: switch.tafa_exampletablet_mikrofon_stumm
    name: Mute microphone
  - entity: select.tafa_exampletablet_nativer_sprachmodus
    name: Voice mode
  - entity: select.tafa_exampletablet_anschlussfragen_ha_grenze
    name: Follow-ups
```

To enable, first select the mode, then turn **mute off**. Always on may also react to background conversations.

## Direct Home Assistant WebSocket commands

Connect to Home Assistant's authenticated **`/api/websocket`**. A custom card running inside HA can use its existing `hass.callWS`; **never hard-code HA tokens into browser-side JavaScript or YAML**.

**Administrator-only write command:**

```json
{
  "id": 41,
  "type": "tablet_assist_for_alexa/device_admin",
  "action": "configure",
  "device_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "settings": {"muted": false, "voice_mode": "wake"}
}
```

The `device_id` is the enrolled Android installation's **32-character ID**, not the HA device registry ID. An HA administrator can retrieve IDs with `tablet_assist_for_alexa/device_admin` and `action:"list"`.

| Desired mode | `settings` |
| --- | --- |
| **Muted** | `{"muted":true}` |
| **Wake word** | `{"muted":false,"voice_mode":"wake"}` |
| **Always on** | `{"muted":false,"voice_mode":"continuous"}` |

Muting does **not** reset the last voice mode. To set an HA follow-up ceiling, send `{"followup_limit":5}`, or `{"followup_limit":-1}` for **no additional HA ceiling**.

Example inside an already-authenticated HA custom card:

```javascript
async function setTafaMicrophone(hass, deviceId, mode) {
  if (!["mute", "wake", "continuous"].includes(mode)) {
    throw new Error("Invalid TAFA microphone mode");
  }
  const settings = mode === "mute"
    ? { muted: true }
    : { muted: false, voice_mode: mode };
  return hass.callWS({
    type: "tablet_assist_for_alexa/device_admin",
    action: "configure",
    device_id: deviceId,
    settings,
  });
}
```

The administrator-only command will fail for non-admin HA accounts. For ordinary users, use the existing HA entities/services and their HA permissions instead.

## Subscribe to per-tablet status changes

The native bridge uses this **read-only, per-device** HA WebSocket subscription:

```json
{
  "id": 42,
  "type": "tablet_assist_for_alexa/device_settings_subscribe",
  "device_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

Only the enrolled device's owner or an HA administrator can subscribe. HA first sends a `result` with `{"subscribed":true}`, then an initial `event` and further events whenever settings change. Example with the control diagnostics extension:

```json
{
  "id": 42,
  "type": "event",
  "event": {
    "device_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "revision": 7,
    "muted": false,
    "voice_mode": "wake",
    "followup_limit": -1,
    "word": "Hey Jarvis"
  }
}
```

Other fields may be present. `revision` is scoped to a HA runtime, not a durable ID across restarts. The Device Bridge uses this read subscription; it does not accept direct network commands from third-party dashboards.

## Diagnostic status and measured switch time

**TAFA → Speak now** shows the control channel (`WebSocket`, `500 ms fallback`, or inactive), whether Android has acknowledged the command, its time of application, and the **HA-to-Android-to-HA round-trip time**. The measured duration includes Android applying the change and sending a separate authenticated acknowledgment; it is **not** one-way WebSocket latency, microphone delay, STT/TTS or Bluetooth playback.

Acknowledgments require **Device Bridge 1.2.3+** and the matching updated HA integration. Older app versions can continue using their existing voice controls but do not provide the new latency fields.

### Follow-up conversations

Explicitly select `Unlimited (until silence)` in the Android app for extended wakeword-free dialogue. In HA, `App-Einstellung` (`followup_limit=-1`) means **no additional HA ceiling**, not permission to override the app's own limit. HA may only reduce it. Silence, errors or muting close an open follow-up; the normal voice mode resumes. Unlimited does not store transcripts.

### Safety and troubleshooting

- `device_admin` write actions require an HA administrator; read subscriptions require the enrolled owner or an HA administrator.
- Never embed a long-lived HA API token in a public dashboard page.
- `unauthorized` means the owner, device ID, or HA permissions do not match.
- If the push socket disconnects, Android reconnects and falls back to authenticated control polling approximately every **500 ms**, plus network overhead.
- Command numbers, acknowledgments and timings are volatile diagnostics; the HA entity state remains authoritative.
