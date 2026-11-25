# TAFA — Tablet Assistant for Alexa

**One Home Assistant App for a local voice-assistant backend.** Install TAFA through Home Assistant Apps, and use the existing **TAFA Device Bridge 1.0.0** on your Android device. The native Android application is **not modified** by this project update.

**English** | [Deutsch](README.de.md)

[![Add TAFA App repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa)

> **Release candidate / developer preview:** TAFA Home Assistant App **0.3.7**, integrated HA component **0.4.1**, Device Bridge **1.0.0 unchanged**. Automated integration, container build and API checks are provided. A complete HA OS fresh-install and physical tablet/audio test is still required before declaring a stable release.

## Quick start — Home Assistant OS

1. Create a Home Assistant backup. Use a test installation first.
2. Settings → Apps → Install app → Repositories: add `https://github.com/michaelbudisch/tablet-assist-for-alexa`.
3. Install and start **TAFA**, then open its built-in Control Center (Ingress).
4. TAFA stages **one** Home Assistant integration at `custom_components/tablet_assist_for_alexa`. Restart Home Assistant once to discover the new component.
5. TAFA downloads a German Piper voice and Faster-Whisper CPU model and checks their actual status. When the speech service and HA are ready, it attempts to configure the TAFA integration and create the **TAFA Lokal** Assist pipeline without overwriting any existing pipelines. Check Control Center if setup needs attention.
6. Connect the unmodified [TAFA Device Bridge 1.0.0](android/README.md) to HA for wake events and playback. Select **TAFA Lokal** in Home Assistant Assist (or the HA Companion app), not in Device Bridge. The Echo is an optional Bluetooth output device, not the microphone.

[Full installation guide](docs/en/app.md) · [Multiroom guide](homeassistant/examples/MULTIROOM.md) · [Android instructions](android/README.md)

## What the one App includes

| Included | Function |
|---|---|
| TAFA Control Center | Ingress setup, real status and guidance |
| Single HA integration | STT/TTS/conversation, HA local intents, optional announcements |
| Native client compatibility | Authenticated `/api/jarvis_tablet_audio/wake_devices`, unchanged routed wake events |
| Multiroom | Independent devices, room audio, optional authorized cameras and motion |
| Vision interfaces | Optional external GPU worker, never enabled automatically |
| Local CPU speech | Piper German TTS + Faster-Whisper German STT in the TAFA App container |
| Automatic setup | HA config flow and a separate TAFA Lokal pipeline, without replacing existing pipelines |
| Safe updates | Only app-owned, unmodified integration files can be updated; previous versions backed up |

The GPU worker, Ollama and Alexa MP3 notifications are **optional**. The app does not bundle or redistribute those models, nor does it install the private dashboard. Model files for CPU speech are downloaded on first start and retained in the app's persistent data volume. Internet access is needed for that initial download.

## Native wake-word handoff — important limitation

Device Bridge 1.0.0 **sends only the recognized wake-word event** and releases its microphone; it does **not** stream the subsequent spoken question. A separate active Assist client (for example Home Assistant's voice interface with microphone permission) must record the question. The TAFA backend alone cannot capture audio that the unchanged Android app never transmits. Manual Assist works independently of wake-word handoff. Fully hands-free use with **only** the TAFA App and Device Bridge 1.0.0 is **not yet supported**. This is a blocker for a stable all-in-one voice release.

## Marketplace alternative

[![Marketplace integration](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration)

Marketplace installs the **same unified TAFA integration 0.4.1**, including the public native-device and multiroom backend. Unlike the Home Assistant App, Marketplace does not provide bundled Piper and Whisper processes. Use your own accessible speech services with that installation. **Do not install the integration through both methods.** [Marketplace guide](docs/en/marketplace.md).

## Safety and migration

- No household-specific hostnames, passwords, tokens, images or private dashboard code are distributed. No microphone or camera is activated without the device owner's action and permissions.
- On a new installation, TAFA maintains a manifest of its installed files and only upgrades copies it owns which have not been edited. It leaves HACS, manual and modified installations untouched. Backups are stored in the HA config's `.tafa/rollback` folder.
- When an older `jarvis_tablet_audio` integration remains configured, the unified component avoids registering duplicate relay endpoints. Legacy setup is **not automatically migrated**; back up first and migrate separately.
- The App and Marketplace use distinct installation mechanisms; the Android APK remains a separate client.

## Documentation

[App setup DE](docs/app.md) · [App setup EN](docs/en/app.md) · [Integration reference](docs/en/marketplace.md) · [Backend changes](docs/en/backend-roadmap.md) · [Security](docs/en/security.md) · [Optional GPU worker](docs/en/worker.md) · [Version history](CHANGELOG.md).

## License

Original project code: [MIT](LICENSE). External libraries, downloaded voice and ASR models are subject to their respective licenses (including Piper licensing). This independent project is not affiliated with Amazon or the Home Assistant project.
