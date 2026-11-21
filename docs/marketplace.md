# Marketplace — Tablet Assist for Alexa

Home Assistant Core 2026.11 or newer. Developer preview 0.2.1. First install on a test instance; do not overwrite a working legacy installation.

## 1. Prepare the speech server

Follow [CPU / Proxmox](proxmox.md) first. The optional [GPU worker](worker.md) is independent. Add the CPU Wyoming integration in Home Assistant (speech server, TCP 10300). If you use the GPU worker for STT, add its Wyoming integration as well and note the separate STT entity.

## 2. Install from the Marketplace

1. In Home Assistant, open **Settings → Marketplace → Add from link** (Einstellungen → Marketplace → Über Link hinzufügen).
2. Enter `https://github.com/michaelbudisch/tablet-assist-for-alexa` and choose **Integration** if a category is requested. Connect GitHub if prompted.
3. Install the available version. The repository has one installable integration at `custom_components/tablet_assist_for_alexa/` and a root-level `hacs.json`. No HACS installer or manual copy into custom_components is needed.
4. Add **Tablet Assist for Alexa** under **Settings → Devices & services → Add integration**. Restart if Home Assistant requests it.

[Open repository in Marketplace](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration) · [Start integration setup](https://my.home-assistant.io/redirect/config_flow_start/?domain=tablet_assist_for_alexa)

## 3. Configuration (no YAML for the integration)

| Field | Example / explanation |
|---|---|
| Piper URL | `http://speechserver.local:5000` (internal host, replace example) |
| CPU Wyoming STT | Select the CPU STT entity |
| GPU streaming URL | Optional, e.g. `http://gpu.local:10502` |
| GPU API key | Optional, from worker configuration; never publish |
| GPU Wyoming STT | Optional, select the second Wyoming entity |
| GPU STT host | Optional host without URL, uses port 10300 for a fast reachability check |
| Conversation agent | Optional existing HA LLM conversation entity, not this router itself |
| Hardware profile | Automatisch = GPU preferred, Homeserver = CPU |
| Live sound profile | Natürlich / Studio / Klar |
| Voice variant | default or 1–9, requires a compatible prepared worker |
| Conversation mode | Manuell / Intelligent / Automatisch |

All addresses and credentials live in the local config entry; reconfigure from the integration menu. CPU Piper must be reachable during setup. GPU and LLM are optional. Settings are global to the integration, not per tablet. Native Home Assistant local intents work when the pipeline prefers local handling; general questions require a configured conversation agent.

Create an Assist pipeline: German language, **Tablet Assist Gesprächsrouter**, **Tablet Assist Sprachrouter**, **Tablet Assist Stream** (or Tablet Assist Piper). Prefer local intents. Select this pipeline in the Android Companion App. See [Bluetooth and Wakeword](home-assistant.md#native-ausgabe-über-amazon-echo-bluetooth). Echo is only the output device, not the microphone. Use Bluetooth for native replies.

## 4. Optional Alexa MP3 announcements

Not needed for Bluetooth. Follow [Nginx proxy, DuckDNS and existing proxy setup](nginx-proxy.md) and configure a compatible notify integration that accepts SSML audio. Configure in the integration:

- MP3 API URL: `http://speechserver.local:5001` (internal only).
- MP3 API key: generated in the speech server's root-only local configuration.
- Public HTTPS audio origin: `https://audio.example.org` (your own certificate-backed domain).
- Room mapping (JSON). Use actual notify entities, and optionally DND and schedule helpers:

```json
{
  "Büro": {
    "notify": "notify.echo_buero_sprechen",
    "dnd": "switch.echo_buero_bitte_nicht_storen",
    "quiet": "schedule.echo_buero_ruhe"
  }
}
```

Supported room names: Büro, Wohnzimmer, Badezimmer, Schlafzimmer, Kinderzimmer. For another room, don't map to a misleading name: custom room names are a future feature. Configured DND / schedule must both be off; unknown/unavailable blocks delivery. Omit a field only if you deliberately do not want that restriction. Unconfigured rooms never receive a message. Only non-confidential messages; HTTPS capability links expire after 15 minutes.

Use the native HA action in automations or developer tools:

```yaml
action: tablet_assist_for_alexa.announce
data:
  text: "Die Waschmaschine ist fertig."
  rooms:
    - Büro
```

The existing German multi-turn announcement dialogue calls this service. The service verifies the MP3 URL, rechecks quiet flags and passes the request to notify. Successful service execution does not prove audible playback on Echo.

## 5. Optional dashboard cards

Register these local resource URLs as JavaScript modules (Settings → Dashboards → Resources, advanced mode):

- `/tablet_assist_for_alexa/assist.js`
- `/tablet_assist_for_alexa/keepalive.js`

Then use a dashboard card with:

```yaml
type: custom:tablet-assist-conversation-card
```

Optional separate card:

```yaml
type: custom:tablet-assist-bt-keepalive
```

The Assist card uses the default pipeline unless you specify an explicit pipeline ID with `pipeline:`. Keepalive is a manually started silent audio loop on that device, not a second microphone. Device compatibility varies; stop if it interferes with Alexa or media.

## Legacy installation / migration

The pre-0.2 manual installer and its dashboard, timer and notification templates remain under `homeassistant/`. They are **not** automatically installed by the Marketplace; create HA automations with the new announce service instead. No automatic import of an existing Jarvis configuration, assistant pipeline, reminders or room rules. Do not mix two active TTS/STT providers with indistinguishable names or remove legacy providers before reconfiguring consumers. Back up and test first. The Marketplace integration uses a new, unique domain and does not replace the old components.

## Status

The installation layout follows the Home Assistant Marketplace custom-repository format. A real setup from Marketplace, live HA API compatibility, GPU inference, Bluetooth audio, and public Alexa HTTPS playback need end-to-end tests. This release is a developer preview, not a claim of official certification or listing in the public catalog.
