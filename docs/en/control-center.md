# TAFA Control Center – responsibilities, setup and integration

[Deutsch](../control-center.md) · [Project](../../README.md) · [Setup](setup-guide.md) · [Custom dashboard development](dashboard-integration.md)

The **TAFA Control Center** is the central configuration UI of the TAFA Home Assistant App, found under **Settings → Apps → TAFA → Open web UI**. It configures the *voice assistant*, not a mandatory dashboard. A user can run TAFA Device Bridge and Home Assistant Assist **without opening or installing any TAFA dashboard**.

## Clear component boundaries

| Component | Owns | Does not own |
| --- | --- | --- |
| **Control Center + HA integration** | Speech pipelines, STT, conversation agents, CPU/GPU routing, TTS, sources, tablet enrollment, rooms and audio | Presentation of a third-party infobox, animation or card duration |
| **TAFA Device Bridge for Android** | Wake word, microphone, native Assist session and Bluetooth/tablet audio | Web infobox design |
| **Optional dashboard** | Voice-state and response display, infobox lifetime and styling, navigation and layouts | Another independent speech/AI pipeline |

The integrated **TAFA Dashboard** is optional. The private, older dashboard still labels its assistant page **Jarvis**; this is a legacy UI name, not a second assistant. **TAFA Dashboard DEV** is a separate development view. Do not ship the private dashboard's household bindings or assume its Jarvis page belongs in the Control Center.

## Control Center sections

Labels may vary slightly between app versions.

| Section | Purpose |
| --- | --- |
| **Overview** | Service and speech-route status, diagnostics |
| **Connections** | GPU worker JSON import and connections, Ollama/Qwen, Whisper/Wyoming, CPU Piper and external audio/HTTPS |
| **Settings** | Speech mode, voice, routing, conversation behavior, AI preferences |
| **Features & sources** | Optional source bindings for weather, energy, heat pumps, fuel, shopping, waste and more |
| **Devices & Multiroom** | Tablet enrollment, user/room pairing, audio devices and camera permissions |
| **Maintenance & Help** | Status, diagnostics and maintenance actions |
| **Speak now** | **Browser-only diagnostic** speech path; it does not verify native Android/Bluetooth audio |

### Voice assistant only, without a TAFA dashboard

1. Install the TAFA App **or** the Marketplace-only integration; never manage both copies of the same integration.
2. Configure the needed CPU/GPU speech endpoints under **Connections** and check the actual STT/TTS integrations in Home Assistant where required.
3. Configure the pipeline and conversation behavior under **Settings**. **Speak now** tests browser audio, not Android's Bluetooth output.
4. Enroll an Android **TAFA Device Bridge** in **Devices & Multiroom**, ideally with a dedicated active **non-admin HA account per tablet/room**.
5. Keep an existing HA dashboard, build your own, or add the optional TAFA Dashboard. **No legacy Jarvis pipeline is required.**

Data sources are optional; missing sensors may be connected later.

## Settings that belong to a dashboard

**Per display:** Whether the display is bound to a speech device at all, selected device, infobox duration and placement, card theme, pictures, animations, and navigation. A desktop browser may remain a passive viewer.

**In core TAFA:** Audio/AI pipeline, speech models, STT/TTS configuration, device registrations and permissions, room routing, and speech-state sensors. Dashboards observe these rather than reimplementing them.

The integrated dashboard stores its presentation preferences in Home Assistant; custom dashboards may store their own layout preferences. Neither should silently overwrite the core voice configuration.

## Multiroom guidelines

- The native Device Bridge has a distinct **32-character installation ID**, not the HA device registry ID.
- Prefer **one non-admin HA room user per device**. A Companion App login can differ, provided the visual display is explicitly bound to the correct device.
- An admin PC must **not** automatically bind to the only registered tablet; an unbound display remains passive even when it sees all HA sensors.
- Route responses using both the **paired device identity** and the **room user**; sharing a HA login is not device identity.
- Device enrollment does not by itself prove that Bluetooth/streaming audio is working.

See [Multiroom setup](../../homeassistant/examples/MULTIROOM.md).

## Integrating your own dashboard

TAFA supplies **authenticated read-only WebSocket APIs** for paired device identity and streamed replies. A question like **“Who was Albert Einstein?”** can become text, images or another type of card; TAFA owns *the answer*, the dashboard owns *the presentation*.

- **[Developer guide: custom dashboards and visual responses](dashboard-integration.md)** – event schema, device-bound response streams, sample code, multiroom isolation, troubleshooting
- **[Dashboard microphone and voice controls](dashboard-voice-control.md)** – standard HA switch/select entities
- **[Data sources and phrases](data-sources.md)**
- **[App installation](app.md)** and [setup](setup-guide.md)

The visual APIs are relatively new. Treat changes to their payloads as compatibility-sensitive and test with several dashboards open simultaneously.

## Common troubleshooting cases

| Symptom | Likely distinction |
| --- | --- |
| Browser test succeeds but Echo is silent | Browser and native tablet/Bluetooth output are different paths |
| Infobox opens on the PC instead of the tablet | Check explicit local device binding and source-device tagging |
| Several spheres animate together | Unbound displays should remain idle; never auto-bind a desktop |
| Weather card opens but knowledge card does not | Check dashboard-specific knowledge/media display preferences |
| The DEV dashboard assistant area is blank | Treat as a separate frontend/component integration issue, not a reason to duplicate the private Jarvis page |
| An automation opens an infobox | This is a **display trigger**, not the assistant's core conversation engine |

**Security and upgrades:** Never publish tokens, personal user/device IDs or household sensor IDs in repository examples. Do not silently overwrite existing user dashboards or HA automations.