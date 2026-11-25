# Manual Home Assistant setup and Android tablet (legacy)

> **TAFA 0.3.10 / integration 0.4.3:** This is the historical manual two-integration Jarvis guide. For new installations do **not** follow the legacy API-token or two-component steps. Instead use [TAFA App with optional external Proxmox speech](app.md) and the [setup guide](setup-guide.md). Private GPU/MP3 services need no additional TAFA API tokens; normal HA authorization is still required.


**English** | [Deutsch](../home-assistant.md) · [Project overview](../../README.md)

The repository contains sanitized legacy integrations and templates. The [Marketplace path](marketplace.md) is recommended for new users; the following is an alternative, not an upgrade procedure.

## Installation on a new instance

1. Back up HA. Add the CPU speech server in Wyoming (IP, port 10300); note its STT entity. Optionally add a GPU Wyoming server.
2. Copy homeassistant/config.example.json to homeassistant/config.local.json and enter your own values. Without GPU leave gpu_host and gpu_stt at their placeholder values. Without an LLM leave llm_agent unchanged. Leave pipeline_id blank until you create the pipeline.
3. Render templates into a new empty staging directory:

```bash
bash homeassistant/install.sh config.local.json ./staging
```

4. Copy custom_components/, www/ and packages/jarvis.yaml from staging into /config without overwriting unrelated files. Add the packages include to configuration.yaml without duplicating an existing homeassistant section:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Check for conflicts with existing helpers and automations. The installer does not upgrade the existing system.

5. Store the generated speech server token in secrets.yaml as piper_api_token. Never commit secrets. Validate HA configuration and restart.
6. Add Jarvis Speech Router and Jarvis Tablet Audio under Settings → Devices & services. Supply a GPU token only if a worker is configured. Check resulting STT and TTS entity IDs.
7. Create a German Assist pipeline: Jarvis conversation router, Jarvis speech router as STT, Jarvis Tablet Stream as TTS, with local intents preferred. Select it in the Companion app. If a different pipeline is the default, add the intended pipeline ID to the configuration JSON and regenerate/copy frontend files.
8. Register these JS resources as modules:
   - /local/jarvis/jarvis-dashboard-assist-v1.4.0.js
   - /local/jarvis/jarvis-bt-keepalive-v1.1.0.js
   - /local/jarvis/jarvis-control-panel-v1.6.0.js
   - /local/jarvis/echo-relay-assist-card-v1.2.0.js

   Also copy `jarvis-settings-v1.1.0.js`, `jarvis-model-settings-v1.1.0.js` and `jarvis-camera-preview-v1.2.0.js`, `jarvis-proactive-v1.0.0.js` into `/config/www/jarvis/`. These modules are imported automatically and need no resource entries.

   Copy the generated jarvis-dashboard.yaml into a new dashboard's YAML editor. No private complete house dashboard is provided. Configure the kiosk/app fullscreen mode in the device browser.

9. Test native speech recognition using known HA intents first, then optional LLM questions, streaming and sound profile changes. Without an LLM, general knowledge questions are unavailable but local intents remain possible. The legacy UI, custom spoken commands and default models remain German.

## Native Amazon Echo output (Bluetooth)

1. Sign in on the tablet using an authorized HA account and configure the Companion app. Grant microphone access only for intended Assist use.
2. Start Bluetooth pairing in the Alexa app for the Echo or ask Echo to pair. Select the Echo under Android Bluetooth settings and connect as media audio.
3. Select the Jarvis Assist pipeline in the HA app. Configure the native wake word/assistant feature where supported; not all Android devices support continuous wake word detection.
4. Ask Assist a normal question. The tablet records audio and Android media output routes the reply to the paired Echo. Echo retains normal Alexa functionality. Its microphone is **not** the input to local Assist requests.
5. Optionally start the Bluetooth keepalive card. It plays a silent loop on that device, not guaranteed to prevent disconnection. It may increase battery use and terminates on a real reload. Test ordinary Alexa use and audio routing. Stop the loop if problems occur.

Bluetooth output requires no publicly accessible MP3. The optional multiroom announcement feature is separate.

## Optional Alexa announcements

In the local JSON configuration set media_player, notify and dnd for each configured room. Notify must support SSML audio. A compatible Alexa integration and valid HTTPS audio origin are required. Do not duplicate normal HA voice responses through an extra Alexa bridge poller.

```json
{
  "buero": {
    "media_player": "media_player.echo_office",
    "notify": "notify.echo_office_speak",
    "dnd": "switch.echo_office_dnd"
  }
}
```

Unconfigured rooms are placeholders and must not produce output. Restrict the HTTPS proxy to expiring 32-character MP3 filenames only. Do not send confidential content. Configure quiet schedules. Automatic notifications start disabled. event_sources maps optional sensor IDs; rules without sources are omitted. The washer requires the matching states of an existing cycle-learning system rather than any power sensor. Verify units and state transitions of other sources. The legacy reminder supports **one** active appointment.

See [Echo Relay Lovelace settings](echo-relay-dashboard.md) for the shared modules and portable dashboard example.
