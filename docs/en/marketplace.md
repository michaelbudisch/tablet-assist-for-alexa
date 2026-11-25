# Marketplace installation — TAFA integration 0.4.2

**English** | [Deutsch](../marketplace.md) · [Project overview](../../README.md)

Marketplace and Home Assistant Apps are two different installation methods. The recommended way to get CPU Piper + Whisper and the TAFA Control Center together is the **[one-App installation](app.md)**. **Do not install both routes on the same Home Assistant instance.**

## What Marketplace installs

Home Assistant Marketplace installs the unified `tablet_assist_for_alexa` integration **0.4.2**, including HA STT, TTS, conversation, optional announcements, native wake-device registration, multiroom/room-audio compatibility APIs, and optional camera/motion and vision interfaces. The old separate `jarvis_tablet_audio` integration is **not required on a fresh install**. The unchanged Device Bridge 1.0.0 is a separate Android application.

Marketplace cannot deploy the running CPU processes. If you install via Marketplace alone, provide a compatible existing Piper HTTP server (with `/health` and `/synthesize`) and either a Wyoming STT entity or a compatible backend supporting `/stt` at the same Piper origin. [CPU server](proxmox.md) · [GPU worker](worker.md). The **TAFA Home Assistant App** bundles compatible CPU Piper/Whisper endpoints instead.

## Installing the integration through Marketplace

1. Back up Home Assistant, ideally test first. Home Assistant Core 2026.11 or later is targeted.
2. Settings → Marketplace → Add from link. Paste `https://github.com/michaelbudisch/tablet-assist-for-alexa`, category Integration.
3. Install and restart Home Assistant if prompted.
4. Settings → Devices & services → Add integration → **TAFA**.
5. Configure an accessible Piper origin, optionally select a Wyoming STT entity, GPU worker, conversation agent and external announcements.
6. Create/select an Assist pipeline with the TAFA STT, conversation and TTS entities. Choose the pipeline in the Home Assistant Assist interface or Companion app, not in Device Bridge.

[Open in HA](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration) · [Start integration setup](https://my.home-assistant.io/redirect/config_flow_start/?domain=tablet_assist_for_alexa)

## Configuration

| Field | Meaning |
|---|---|
| Piper origin | Compatible local Piper HTTP API, e.g. `http://speechserver.local:5000` |
| CPU STT entity | Optional Wyoming STT entity; without it, TAFA uses `/stt` on the Piper origin |
| GPU streaming URL | Optional private-LAN Qwen streaming service; no extra API token |
| GPU STT entity / host | Optional acceleration, with fallback to CPU |
| Conversation agent | Optional existing HA agent for general knowledge |
| Audio profile and voice | Optional preferences |
| MP3 announcement settings | Optional HTTPS MP3 generator and room mapping |

No custom YAML or private dashboard is necessary for the shared integration. Interface labels are DE/EN; shipped local voice commands and CPU models are German. Android camera/microphone permissions and wake-word activation remain under Device Bridge.

## Existing installations, updates and limitations

- Do not overwrite a configured `jarvis_tablet_audio` installation. The unified backend detects old config entries and avoids duplicate legacy REST and service registration. Existing room assignments and storage do **not** migrate automatically.
- App-managed component files are never overwritten by a Marketplace install. If you choose Marketplace, manage integration updates there and do not also let the TAFA App manage its code.
- New version **0.4.2** merges public native relay modules; private household dashboard and its resources are excluded. Optional GPU services remain external.
- Automated validation includes source/static tests, HACS/hassfest, and HA runtime workflow; physical Device Bridge, Bluetooth, concurrent multiroom, and clean HA OS installation are still outstanding. Treat this as a **release candidate**, not a validated stable release.

[App installation](app.md) · [Backend integration](backend-roadmap.md) · [Security](security.md) · [Multiroom](../../homeassistant/examples/MULTIROOM.md).
