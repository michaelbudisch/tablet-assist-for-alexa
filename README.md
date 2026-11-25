# TAFA — Tablet Assistant for Alexa

**One Home Assistant App for a local voice-assistant backend.** Install TAFA through Home Assistant Apps, and use the existing **TAFA Device Bridge 1.0.0** on your Android device. The native Android application is **not modified** by this project update.

**English** | [Deutsch](README.de.md)

> **New in App 0.3.12:** Manage TAFA settings exclusively at **Settings → Apps → TAFA → Configuration**; restart the App after saving. On upgrade, restart HA Core once for integration 0.4.4, then restart the App to sync existing settings. Add the native Wyoming integration once in Devices & services, but choose its TAFA entity and configure all other TAFA options in the App. Existing Assist pipelines are preserved. Marketplace-only installations retain their HA options flow.


[![Add TAFA App repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa)

> **Release candidate / developer preview:** TAFA Home Assistant App **0.3.12**, integrated HA component **0.4.4**, Device Bridge **1.0.0 unchanged**. Automated integration, container build and API checks are provided. A complete HA OS fresh-install and physical tablet/audio test is still required before declaring a stable release.

**[Simplified setup guide: TAFA local, Proxmox, GPU and Alexa HTTPS](docs/en/setup-guide.md)**

## Proxmox: one combined speech and Nginx CT

A guided **one-line Proxmox host installer** creates one **new** unprivileged Debian LXC with Piper, Wyoming-Whisper, a private token-free MP3 generator, and an Nginx frontend. Existing containers and VMs remain untouched.

```bash
curl -fsSLo /root/tafa-pve-install.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/quick-install.sh && bash /root/tafa-pve-install.sh
```

Run as root in an interactive **Proxmox host shell**. Choose the CT ID, storage, network, resources and optional GPU worker/HTTPS hostname, then explicitly confirm the CT ID. The guest console provides a persistent address/status banner. Use `tafa-info` for diagnostics and `tafa-setup` to complete Alexa HTTPS once DNS and routing are ready. [Complete guide](docs/en/proxmox.md).

## Quick start — Home Assistant OS

1. Create a Home Assistant backup. Use a test installation first.
2. Settings → Apps → Install app → Repositories: add `https://github.com/michaelbudisch/tablet-assist-for-alexa`.
3. Install and start **TAFA**, then open its built-in Control Center (Ingress).
4. TAFA stages **one** Home Assistant integration at `custom_components/tablet_assist_for_alexa`. Restart Home Assistant once to discover the new component.
5. **Before starting the App**, select `speech_mode=local` (CPU Piper/Whisper bundled) or `speech_mode=external` with `external_piper_base=http://PROXMOX-IP:5000` in App Configuration. External mode skips all bundled CPU models. Then add Proxmox Wyoming STT (`PROXMOX-IP:10300`) in HA, select it in Apps → TAFA → Configuration, and create an Assist pipeline. Local mode retains automatic **TAFA Lokal** pipeline creation.
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

Marketplace installs the **same unified TAFA integration 0.4.3**, including the public native-device and multiroom backend. Unlike the Home Assistant App, Marketplace does not provide bundled Piper and Whisper processes. Use your own accessible speech services with that installation. **Do not install the integration through both methods.** [Marketplace guide](docs/en/marketplace.md).

## Safety and migration

- No household-specific hostnames, passwords, images or private dashboard code are distributed. No microphone or camera is activated without the device owner's action and permissions.
- On a new installation, TAFA maintains a manifest of its installed files and only upgrades copies it owns which have not been edited. It leaves HACS, manual and modified installations untouched. Backups are stored in the HA config's `.tafa/rollback` folder.
- When an older `jarvis_tablet_audio` integration remains configured, the unified component avoids registering duplicate relay endpoints. Legacy setup is **not automatically migrated**; back up first and migrate separately.
- The App and Marketplace use distinct installation mechanisms; the Android APK remains a separate client.

## Documentation

[App setup DE](docs/app.md) · [App setup EN](docs/en/app.md) · [Integration reference](docs/en/marketplace.md) · [Backend changes](docs/en/backend-roadmap.md) · [Security](docs/en/security.md) · [Optional GPU worker](docs/en/worker.md) · [Version history](CHANGELOG.md).

## License

Original project code: [MIT](LICENSE). External libraries, downloaded voice and ASR models are subject to their respective licenses (including Piper licensing). This independent project is not affiliated with Amazon or the Home Assistant project.
