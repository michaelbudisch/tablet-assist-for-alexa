# Install the TAFA Home Assistant App

[Deutsch](../app.md) · [Project](../../README.md) · [Complete setup guide](setup-guide.md) · [WebSocket controls](dashboard-voice-control.md)

TAFA provides a **Control Center**, one integrated HA component, and optional CPU Piper/Faster-Whisper services. It requires **Home Assistant OS 2026.11+** with Apps on `amd64` or `aarch64`.

## Fresh installation

1. Back up Home Assistant. Under **Settings → Apps → Install app → Repositories**, add `https://github.com/michaelbudisch/tablet-assist-for-alexa`.
2. Install and start **TAFA**. New installations use `speech_mode=setup`: CPU models **are not downloaded automatically**. In **Control Center → Settings**, explicitly choose **Local** (Piper/Whisper inside TAFA) or **External** (compatible speech server).
3. For **External**, enter the CPU Piper HTTP origin in **Connections → CPU fallback**. Add the HA **Wyoming Protocol** integration for the CPU speech host on port 10300; then choose its `stt.*` entity in **TAFA → Connections**. For **Local**, select Local, save and restart the App to download/start bundled models.
4. TAFA provisions `custom_components/tablet_assist_for_alexa`. **Restart Home Assistant Core once**, check the TAFA integration under **Devices & services**, and restart TAFA if necessary. Do **not** install a second Marketplace-managed copy.
5. Under **Settings → Voice assistants**, check **TAFA Lokal**: **Tablet Assist Sprachrouter** (STT), **Tablet Assist Gespraechsrouter** (conversation), **Tablet Assist Stream** (TTS). Set up missing backend entities before creating the pipeline; existing pipelines are retained.
6. Install and connect the [signed Device Bridge](../../android/README.md) for native wake word and audio. Continue with the [setup guide](setup-guide.md).

## Control Center areas

| Area | Purpose |
| --- | --- |
| **Overview** | Voice route status and next-step guidance |
| **Connections** | **Quick JSON setup**, GPU IP/fast check, GPU Whisper/Qwen/Ollama, CPU Piper/Wyoming and Alexa MP3/HTTPS |
| **Settings** | Speech mode, routing, voice, conversation behavior, optional features |
| **Devices & Multiroom** | Tablet enrollment, accounts, rooms and camera permissions |
| **Maintenance & Help** | Diagnostics, backend/models and restart |
| **Speak now** | Separate **browser voice test** with Muted/Wake word/Always on, transcript, answer and timing; needs HTTPS/localhost for browser microphone |

**Note:** Successful HTTP/TCP checks prove network reachability, not speech recognition or Bluetooth playback. **Speak now** is a browser playback/diagnostic test; native Android/Echo playback is tested in Device Bridge.

## Features & sources – no JSON required

Open **TAFA Control Center → Features & sources**. New modules become available after updates without overwriting existing dashboard tiles or automations.

1. Open a feature, for example **Fuel & tank**.
2. Choose a Home Assistant sensor by its friendly name. TAFA validates its domain and measurement unit.
3. **Save sources**: speech queries use the sensor. The built-in dashboard uses the same assignment when no custom tile binding exists.
4. **Add to TAFA dashboard** activates a missing module while keeping existing tiles.
5. Missing integrations may be installed later under **Settings → Devices & services**. Other features keep working.

Alexa announcements also use graphical room selectors. An installed notify service is required. Additional output rooms can be created; native tablet pairing remains under **Devices & multiroom**.

The internal sources_json and rooms_json formats are retained for compatibility but are no longer required in the normal setup UI.

**Updates:** TAFA stores dashboard preferences separately from program code. Supported fields of older configurations are recovered individually, and the previous stored version is backed up before saving. Private Lovelace dashboards and existing automations are not changed.

## Updates and existing installations

TAFA only updates intact integrations **originally managed by the App** and saves backups in `<HA config>/.tafa/rollback`. Marketplace/HACS/manual integrations are not overwritten. Restart HA Core once after backend updates. Existing automations, custom dashboards and other Assist pipelines are not silently modified.

See [Proxmox](proxmox.md) for an optional CPU server, [GPU worker](worker.md) for optional acceleration, and [Marketplace-only integration](marketplace.md) if not installing the App. [Legacy Jarvis instructions](home-assistant.md) are **not** for a fresh setup.

**Security:** Keep CPU and GPU services on a trusted LAN. No extra TAFA worker API tokens are required for the modern LAN endpoints, but ordinary Home Assistant authentication and permissions still apply.
