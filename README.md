# TAFA · Tablet Assistant for Alexa

![TAFA architecture overview with Android phone, tablet, Home Assistant, local AI and Echo](docs/tafa-architecture.jpg)

**English** | [Deutsch](README.de.md)

**Your local AI voice assistant for Home Assistant — powered by an Android tablet and an Echo speaker.**

![Developer Preview](https://img.shields.io/badge/Status-Developer%20Preview-orange) ![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-03a9f4) ![Local AI](https://img.shields.io/badge/AI-Local-0f766e)

TAFA combines local speech recognition, Home Assistant data, optional AI models and natural speech. An Android tablet acts as the microphone and interface; the Echo retains its ordinary Bluetooth and Alexa functions.

## Marketplace scope and backend roadmap

The current link installs the `tablet_assist_for_alexa` base integration only. The separate `jarvis_tablet_audio` backend (multiroom, device registration, native wake-word routing and camera/vision interfaces) is not installed by this link. Marketplace supports one integration per repository; the target is a single configurable domain with these backend capabilities ported and tested, while retaining documented compatibility with Device Bridge 1.0.0. External CPU/GPU speech servers and the Android APK remain separate installations. The private TAFA dashboard, its assets and household configuration are excluded. Do not install a second integration over a working system or assume automatic migration. See the [backend consolidation plan](docs/en/backend-roadmap.md).

## Features at a glance

| Area | Capabilities |
|---|---|
| Voice | Whisper STT, wake word, conversation, follow-up questions |
| Audio | CPU Piper, optional Qwen streaming, TAFA Device Bridge via Bluetooth |
| Home control | Native HA intents, weather, energy, heating, Bring!, waste collection, reminders |
| AI | Optional local Ollama LLM, model and context settings |
| Native Android app | Echo Relay, Bluetooth streaming, front/rear camera, optional image-motion detection for HA |
| Vision | Local still-image description, camera preview, optional structured motion detection |
| HA automations | Reusable speech action with acknowledgement, weather advice, greeting, test timer |
| Family | Three optional name helpers; no identity recognition |
| Announcements | Optional Alexa MP3 announcements via temporary HTTPS links |

**Tested in the existing private home dashboard:** native Bluetooth playback, HA speech action, personalized greeting and automatic test-timer cancellation. The generic infobox is installed there; the Ring workflow and standalone updated card still need end-to-end testing.

> **Developer preview:** base integration 0.3.1, backend 1.7.1, GPU Worker 2.2.0 (updated schema), APK 1.0.0. Optional card 1.3.0 and automation templates are not a fully verified fresh-install release. A GPU is not required for the CPU setup.

## New: native HA automations

[Set up automation templates and family settings](docs/en/ha-automations.md). The dashboard edits names while Home Assistant owns conditions, weather and time windows. Vision categories are fallible visual estimates, not facial or identity recognition. Enable automatic image analysis only with informed consent from affected people.

## Architecture

Home Assistant is the central controller. The Android device handles voice input, camera capture and Bluetooth audio output through the native TAFA Device Bridge app.

**Voice:** Android microphone → Home Assistant Assist → Whisper (STT) → conversation router → local HA intents or LLM → Piper or Qwen (TTS) → TAFA Device Bridge on Android → Bluetooth → Amazon Echo.

**Camera & motion:** Android front/rear camera → Home Assistant (camera entity and motion sensor) → optional vision worker → image description or HA detection event.

**Automations:** HA event → conditions and actions → optional voice announcement via Echo Relay.

The CPU baseline uses Whisper and Piper without a dedicated graphics card. An optional GPU worker adds accelerated STT, Qwen streaming TTS, local Ollama language models and vision. Alternatively, Alexa announcements can use an MP3 API and HTTPS proxy.

## Home Assistant Marketplace

[![Open in Home Assistant Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration)

Home Assistant 2026.11+: Settings → Marketplace → Add from link → `https://github.com/michaelbudisch/tablet-assist-for-alexa` → Integration. Configure Tablet Assist for Alexa in Devices & services. Speech servers are installed separately.

The Marketplace integration includes STT, TTS, conversation routing and the optional announcement action, without editing source files or YAML. Legacy control-panel, timer and automatic notification examples remain available under homeassistant/; Marketplace does not install them automatically.

After setup, a dedicated **Tablet Assist** sidebar panel is registered automatically, with native Assist launch, service status, optional Alexa announcements and Bluetooth keepalive. No legacy helper or private dashboard is required. Configuration and pipeline selection remain in Home Assistant.

## Native Android app: audio, camera and motion

**[TAFA Device Bridge 1.0.0](android/README.md)** provides a German/English Android audio player with HA discovery, one-time token QR scanning, verified Bluetooth output and optional native silent keepalive. [Download the signed APK](android/downloads/TAFA-Device-Bridge-1.0.0.apk). The standalone [Echo Relay Assist Lovelace card](docs/en/echo-relay-dashboard.md) connects the app to any HA dashboard. Set up the command/status helpers separately; the Marketplace integration does not configure them automatically.

The app is more than an audio player: it can expose the front or rear camera of an Android smartphone or tablet to Home Assistant. With explicit permission, the app supplies periodically refreshed still images; HA exposes a camera entity and an optional image-motion sensor. The local vision worker supports authorized camera questions and HA automations. Camera capture is independent of audio playback, must be explicitly started and does not automatically resume after device reboot. Images are not archived. These are refreshed stills, not a full-rate live video stream. [Android camera details](android/README.md#camera-and-local-vision).

## Multiroom · backend 1.7.0

[**Full Multiroom setup guide including TAFA kiosk room-audio compatibility**](homeassistant/examples/MULTIROOM.md) · [Deutsch](homeassistant/examples/MULTIROOM.de.md)

One Home Assistant for multiple tablets, each with a dedicated non-admin room account, independent Echo Relay audio, optional camera/motion entities and adjustable image refresh rate. Room management supports provisioning, quiet hours and targeted announcements. The room assistant requires the same account in the app and HA dashboard, and trusted HTTPS for microphone input. No legacy audio helpers are needed in room mode. One physical tablet and automated two-room checks passed; concurrent physical two-tablet and clean-install tests remain outstanding. The Marketplace base integration does not automatically install this separate backend.

## Local HTTPS for the tablet microphone

With an existing NGINX/Certbot proxy, [optional split DNS](docs/en/local-https.md) lets the tablet reach HA through the **same trusted HTTPS hostname** directly over the LAN, even when the WAN is offline. No second proxy, router-port changes or hardcoded IP in the TAFA dashboard. Existing public sites are not automatically secured by split DNS.

## Installation guides

```bash
git clone https://github.com/michaelbudisch/tablet-assist-for-alexa.git
cd tablet-assist-for-alexa
```

| Guide | Description |
|---|---|
| [CPU speech server / Proxmox](docs/en/proxmox.md) | Local CPU speech services |
| [Marketplace and configuration](docs/en/marketplace.md) | HA integration and setup |
| [Android tablet / Bluetooth](docs/en/home-assistant.md) | Manual legacy setup |
| [Multiroom setup](homeassistant/examples/MULTIROOM.md) | Room accounts, audio, camera, HTTPS and troubleshooting |
| [Echo Relay dashboard](docs/en/echo-relay-dashboard.md) | Lovelace installation |
| [HA automations](docs/en/ha-automations.md) | Family settings and reusable speech |
| [Optional GPU computer](docs/en/worker.md) | Windows/Linux, STT, TTS, local AI |
| [Optional Nginx proxy](docs/en/nginx-proxy.md) | DuckDNS and Certbot |
| [Local HTTPS / split DNS](docs/en/local-https.md) | Existing NGINX, trusted tablet microphone and LAN access without WAN |
| [Local data sources](docs/en/data-sources.md) | Voice commands and supported entities |
| [Security / privacy](docs/en/security.md) | Network and privacy boundaries |
| [Tests and release checklist](docs/en/release.md) | Validation status |
| [Version history](CHANGELOG.md) | Changelog |

Use installers for **new installations**; they do not migrate an existing Jarvis setup. Do not overwrite production configuration. Configure your own hosts, speaker entities and secrets locally. The Nginx installer also has a shared-proxy mode for a new unused hostname on an existing proxy.

## License

MIT for original project code; see [LICENSE](LICENSE). Dependencies and separately downloaded models remain subject to their own licenses: [Piper](https://github.com/OHF-Voice/piper1-gpl), [Wyoming Faster Whisper](https://github.com/OHF-Voice/wyoming-faster-whisper), [Home Assistant](https://www.home-assistant.io/), [Faster Qwen3 TTS](https://github.com/andimarafioti/faster-qwen3-tts), [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), [FFmpeg](https://ffmpeg.org/), [Ollama](https://ollama.com/). Models and voices are not bundled. Check model cards and license terms before use. Independent community project, not affiliated with or endorsed by Amazon. Alexa and Echo are trademarks of their respective owners.
