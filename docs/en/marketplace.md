[Deutsch](../marketplace.md) | **English** · [Project overview](../../README.md)

# Marketplace — Tablet Assist for Alexa

Home Assistant Core 2026.11 or newer. Developer preview 0.3.1. Start on a test instance and do not overwrite a working legacy configuration.

**New in 0.3.1:** Local intent recognition, configurable weather, Bring!, collection, heating and energy sources, and a persistent reminder dialogue. [Data sources and voice commands](data-sources.md).

**New:** Contextual follow-ups and optional administrator-approved aliases. [Guide](data-sources.md).

## 1. Prepare the speech server

Follow the [CPU / Proxmox setup](proxmox.md). The [GPU worker](worker.md) is optional. Add the CPU Wyoming integration (speech server host, TCP 10300). If using GPU STT, add its separate Wyoming integration as well and note its entity.

## 2. Install from Marketplace

1. Open Settings → Marketplace → Add from link.
2. Enter `https://github.com/michaelbudisch/tablet-assist-for-alexa` and select Integration if prompted. Connect GitHub if requested.
3. Install the available version. The repository has one integration in `custom_components/tablet_assist_for_alexa/` and a root-level `hacs.json`. No manual copying is needed for the Marketplace installation.
4. Go to Settings → Devices & services → Add integration → Tablet Assist for Alexa. Restart if required.

[Open in Home Assistant](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration) · [Start integration setup](https://my.home-assistant.io/redirect/config_flow_start/?domain=tablet_assist_for_alexa)

## 3. Configure without YAML

| Field | Example / description |
|---|---|
| Piper URL | `http://speechserver.local:5000` (replace with your internal host) |
| CPU Wyoming STT | Select the CPU STT entity |
| GPU streaming URL | Optional, e.g. `http://gpu.local:10502` |
| GPU API key | Optional, from the worker's local configuration |
| GPU Wyoming STT | Optional second Wyoming entity |
| GPU STT host | Optional hostname for a reachability check on port 10300 |
| Conversation agent | Optional HA LLM conversation entity, not this router itself |
| Hardware profile | Automatic: GPU preferred; Homeserver: CPU |
| Live sound profile | Natural / Studio / Clear |
| Voice variant | Default or 1–9, with compatible prepared worker |
| Conversation mode | Manual / Intelligent / Automatic |

Addresses and credentials are stored locally in the config entry. Use its Reconfigure menu to change them. Piper must be reachable during setup. GPU and LLM are optional. Settings apply to the integration, not individual tablets.

**Speech language:** The shipped speech pipeline and custom voice-command grammar are currently German. English documentation and UI labels do not mean English speech recognition, synthesis or announcement dialogue has been implemented. The bundled installer loads German voice models. For native local intents, enable local-intent priority; general knowledge questions require a configured conversation agent.

Create an Assist pipeline with German language, the Tablet Assist conversation router, STT router and Stream (or Piper) TTS. Select the pipeline in the Android Companion app. See [Bluetooth and wake word](home-assistant.md#native-amazon-echo-output-bluetooth). Echo is the output speaker, not the microphone.

## 4. Standalone voice center (automatic)

After successful integration setup, **Tablet Assist** appears in the Home Assistant sidebar at `/tablet_assist_for_alexa`. This is a dedicated integration panel, not an editable Lovelace dashboard. It needs no private house dashboard, legacy helpers or manual resource registration. It contains native Assist launch, speech service status, administration shortcuts, Bluetooth keepalive and announcements to configured rooms. The Companion app opens native Assist; a normal browser uses the default dashboard's Assist as a fallback. Select the correct pipeline. The panel follows the HA interface language and is removed when the integration unloads. Real device rendering and native app launch still require testing.

## 5. Optional Alexa MP3 announcements

Not needed for Bluetooth. Follow [Nginx, DuckDNS and existing proxy setup](nginx-proxy.md) and configure a compatible notify integration that supports SSML audio.

- MP3 API URL: internal `http://speechserver.local:5001`.
- MP3 API key: generated in the CPU speech server's root-only configuration.
- Public HTTPS audio origin: your own certificate-backed hostname, e.g. `https://audio.example.org`.
- Room mapping JSON. The existing German room keys are stable internal identifiers, even in the English interface; use actual notify entities and optional DND and schedule helpers.

```json
{
  "Büro": {
    "notify": "notify.echo_office_speak",
    "dnd": "switch.echo_office_dnd",
    "quiet": "schedule.echo_office_quiet"
  }
}
```

Supported keys: Büro (office), Wohnzimmer (living room), Badezimmer (bathroom), Schlafzimmer (bedroom), Kinderzimmer (children's room). Other room names are not supported yet. Configured DND and schedule flags must be off; missing/unavailable configured flags block delivery. Omit a flag only if you deliberately do not need that restriction. Unconfigured rooms receive nothing. Share no confidential messages: the HTTPS file link expires after 15 minutes.

Use the action in automations or developer tools:

```yaml
action: tablet_assist_for_alexa.announce
data:
  text: "Die Waschmaschine ist fertig."
  rooms:
    - Büro
```

Use text compatible with the installed voice. The German multi-turn announcement dialogue calls this service. It verifies the returned audio path, rechecks room restrictions and calls notify. Successful service execution does not establish audible playback on Echo.

## 6. Optional cards for other dashboards

Only if you want additional dashboard cards, register these local URLs as JavaScript module resources (Settings → Dashboards → Resources, advanced mode):

- `/tablet_assist_for_alexa/assist.js`
- `/tablet_assist_for_alexa/keepalive.js`

Add a dashboard card:

```yaml
type: custom:tablet-assist-conversation-card
```

Optional separate card:

```yaml
type: custom:tablet-assist-bt-keepalive
```

The Assist card uses the last-used pipeline unless `pipeline:` specifies a pipeline ID. Both cards follow the HA interface language (German or English). Keepalive is a manually started silent audio loop on the tablet, not a second microphone. Compatibility varies; stop if it interferes with Alexa or media playback.

## Legacy installation / migration

The pre-0.2 manual installer, dashboard, timer and notification templates remain in `homeassistant/`. They are **not** installed automatically by Marketplace. Create new HA automations with the announcement action instead. Existing Jarvis settings, pipelines, reminders and room rules are not imported automatically. Do not remove legacy providers until their consumers have been reconfigured. Back up and test first. The Marketplace integration has its own domain and does not overwrite the older components.

## Status

The layout follows the Marketplace custom-repository format. Fresh Marketplace installation, live HA API compatibility, GPU inference, Bluetooth and public HTTPS playback still require end-to-end testing. This is a developer preview, not an official certification or public catalog listing.
