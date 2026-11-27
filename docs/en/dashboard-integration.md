# Developer API: integrate TAFA into your own dashboard

[Deutsch](../dashboard-integration.md) · [Control Center](control-center.md) · [Microphone controls](dashboard-voice-control.md) · [Multiroom](../../homeassistant/examples/MULTIROOM.md)

Use TAFA as a **standalone local voice assistant** and build your own Home Assistant dashboard. The TAFA/Android voice path continues to work without an open or installed dashboard. These **recent** visual WebSocket APIs are intended for custom frontends and should be handled with compatibility checks.

## Boundaries

| Component | Responsibilities |
| --- | --- |
| **TAFA Control Center and HA integration** | STT, conversation model, TTS, optional data sources, room and device administration |
| **TAFA Device Bridge on Android** | Wake-word detection, native Assist session, microphone and Bluetooth/tablet playback |
| **Your dashboard** | Optional display of voice phases and responses, card lifetime, layout, images and animations |

Neither the private dashboard's old **Jarvis** menu nor the **TAFA Dashboard DEV** page is required for custom integrations. **Do not** send a second request to Ollama just to create a visual card: subscribe to the response TAFA already generated.

## 1. Read the device identity

From an authenticated Home Assistant custom element:

```js
const {devices} = await hass.callWS({
  type: "tablet_assist_for_alexa/visual_identity",
});
```

Each authorized paired device has a record of this form (example identifiers only):

```json
{
  "devices": [{
    "device_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "room": "office",
    "label": "Office",
    "user_id": "room_account_id",
    "sensors": {
      "status": "sensor.tafa_example_wake_status",
      "mic": "sensor.tafa_example_microphone",
      "last": "sensor.tafa_example_last_wake"
    }
  }]
}
```

- `device_id` is the **32-character Android Device Bridge registration ID**, not HA's device registry ID.
- `room` is the paired audio room ID; `label` is a human-facing device name and **may differ**.
- `user_id` is the HA account used by that paired room.
- The sensor values are the actual HA entity IDs and avoid guessing names.
- A non-admin HA user sees only their paired devices. Admins may see multiple devices.

Select a device **per browser/WebView** or choose **No voice device (display only)**. Do not silently bind a desktop PC to the only Android tablet; a desktop without its own pairing must stay passive. A Companion App account may be different from the room account, provided the display is explicitly bound.

## 2. Subscribe to device-scoped responses

Use the existing authenticated `hass.connection` and keep **one** subscription per active visual component:

```js
async function subscribeTafaResponses(hass, selectedDeviceId, showCard) {
  const {devices} = await hass.callWS({
    type: "tablet_assist_for_alexa/visual_identity",
  });
  const device = devices.find(d => d.device_id === selectedDeviceId);
  if (!device) return () => {}; // No binding: passive screen

  return hass.connection.subscribeMessage(packet => {
    const data = packet?.event?.data || packet?.event || packet?.data || packet;
    // A shared HA admin account is not an identity for one physical display.
    if (data?.tafa_device_id !== device.device_id) return;
    if (data?.user_id !== device.user_id) return;
    if (typeof data.reply !== "string" || !data.reply.trim()) return;
    showCard({
      title: data.topic === "knowledge" ? "Knowledge"
           : data.topic === "weather" ? "Weather" : "TAFA",
      question: data.question || "",
      message: data.reply,
      topic: data.topic || "knowledge",
    });
  }, {type: "tablet_assist_for_alexa/visual_subscribe"});
}

// In disconnectedCallback() and whenever the selected device changes:
// const unsubscribe = await subscribeTafaResponses(...);
// unsubscribe?.();
```

**Payload:** `question` (spoken text), `reply` (answer), `topic` (`knowledge`, `weather`, `search` etc.), `user_id` (room HA user), `device_id` (original HA Assist ID, **not** native pairing identity), `tafa_device_id` (TAFA server's native pairing ID), and optional `sources` or search metadata. `tafa_device_id` can be **empty** if the source cannot be uniquely mapped; in that case **do not broadcast or guess a device**. Non-admin subscriptions are restricted to the user's paired room, but the UI must additionally enforce the selected local device.

`hass.connection.subscribeMessage()` resolves to an unsubscribe function. Close subscriptions when the element disconnects, when the websocket reconnects, or when changing the selected device. A simple question such as **“Who was Albert Einstein?”** does **not** require creating any HA automation.

## 3. Show voice phases using the paired sensor IDs

```js
const wake = hass.states[device.sensors.status]?.state || "";
const mic  = hass.states[device.sensors.mic]?.state || "";
const speaking = /^native_(speaking|playing|buffering)/.test(wake)
  || /^(speaking|playing|tts)$/i.test(mic);
```

Other common stages include `native_processing` and `native_listening`; consumers must tolerate unknown statuses. `listening: hey_jarvis` normally means **wake-word standby**, not active listening. Never substitute the first sensor in HA's global state list for a locally bound sensor.

## 4. Presentation is optional and owned by your UI

Set card duration, layout, media, navigation and animation in the **dashboard**, not in the TAFA Control Center. One UI may display only a text response; another can show an infobox or an ambient sphere. Optional Wikipedia images must be retrieved and rendered by the UI: TAFA does not guarantee an image with every reply.

Proactive automation notifications are a separate use case from speech replies. The old private event `jarvis_infobox_show` is **not a required TAFA core API** and should not be a dependency of a fresh custom-dashboard integration.

## 5. Microphone buttons and room setup

Use ordinary HA switch/select entities for mute, wake vs. always-on, and follow-up settings. See [dashboard microphone controls](dashboard-voice-control.md). The visual subscription is **read-only** and does not modify microphone settings.

For each Android tablet, use a distinct active **non-admin HA room user**, and pair it to a room through Control Center. Audio room pairing and device registration are different steps. See [Multiroom setup](../../homeassistant/examples/MULTIROOM.md).

## 6. Testing with a tablet and an admin PC

1. On **both** screens, read `visual_identity`; the admin PC may list more devices.
2. Bind the Android screen to its unique Device Bridge ID, the PC to **No voice device**.
3. Ask “Who was Albert Einstein?” and “What is the weather?” **on the tablet**.
4. Both answers and voice-phase animation should appear **only on the selected tablet**.
5. Verify the response contains a matching `tafa_device_id` and `user_id`. If device tagging is empty, check Control Center → Devices & Multiroom, not name-based heuristics.
6. For missing Echo output, inspect the Android/Bluetooth player instead of infobox code.

## Security and upgrades

Keep your HA authentication in the host app; **never embed tokens** in Lovelace JS, YAML or public GitHub examples. Do not publish personal room IDs, device IDs, or household sensor names. The API payload is not itself permission to read arbitrary HA entity values. Keep existing user dashboards and automations intact across updates.