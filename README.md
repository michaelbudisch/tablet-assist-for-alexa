# TAFA — Tablet Assistant for Alexa

**One Home Assistant App for a local voice-assistant backend.** Install TAFA through Home Assistant Apps, and use the existing **TAFA Device Bridge 1.0.1** on your Android device. The native Android application is **not modified** by this project update.

**English** | [Deutsch](README.de.md)

> **From App 0.3.24:** Fresh installations start in **setup mode without speech-model downloads**. Install the GPU Worker or Proxmox speech server, export its JSON, then preview and confirm it in **TAFA Control Center → Settings**. TAFA configures supported integrations and completes the TAFA Lokal Assist pipeline when its components are ready. A newly staged HA integration may need a separately authorized one-time Core restart; the approved import resumes afterwards.


[![Add TAFA App repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa)

> **Release candidate / developer preview:** TAFA Home Assistant App **0.3.27**, HA integration **0.4.13**, Device Bridge **1.0.1**. Automated integration, container build and API checks are provided. A complete HA OS fresh-install and physical tablet/audio test is still required before declaring a stable release.

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
6. Connect the unmodified [TAFA Device Bridge 1.0.1](android/README.md) to HA for wake events and playback. Select **TAFA Lokal** in Home Assistant Assist (or the HA Companion app), not in Device Bridge. The Echo is an optional Bluetooth output device, not the microphone.

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

**Tablet Multiroom (new):** Admins can now pair registered tablets directly in **TAFA → Devices**, choosing an existing non-admin HA user and audio room, with live connection status. No Developer tools/YAML. The Android 1.0.0 app is unchanged. [Guided setup](docs/en/setup-guide.md).

**New: integrated voice test.** Under **TAFA → Devices → Voice test**, speak through the browser microphone and listen to the Qwen/Piper response on the paired tablet. Requires trusted HTTPS and a full Assist pipeline; Android app unchanged. [Instructions](docs/en/setup-guide.md).

**New in App 0.3.15 / integration 0.4.7:** **TAFA → Devices → Voice test** includes audio-only Qwen/Piper to Android playback verification that works on local HTTP. The full microphone test still requires HTTPS. [Guide](docs/en/setup-guide.md).

**New in TAFA 0.3.16 / integration 0.4.8:** External Proxmox setup checks for Wyoming STT and a complete Assist pipeline before reporting ready. A single Wyoming STT provider is selected automatically; with multiple providers, choose `cpu_stt` in TAFA App Configuration. See the optional native Android 1.0.1 microphone setup under **TAFA → Devices**. [Setup](docs/en/setup-guide.md).

**New:** TAFA Control Center lets you assign discovered Wyoming STT entities to CPU/GPU dropdowns. **GPU Worker 2.2.2** provides a complete DE/EN setup and connection TXT (`04-Verbindungsdaten.bat`), including the separate Ollama conversation integration. [Setup guide](docs/en/setup-guide.md).

**TAFA App 0.3.19 hotfix:** Add the missing Wyoming picker to the Docker build. Update/rebuild the TAFA App; the existing configuration and Android app remain unchanged.

**TAFA 0.3.21 / GPU Worker 2.2.3:** TAFA now shows safe private endpoint reachability and the last observed STT routing backend where available. The worker-generated TXT contains only the three relevant GPU PC endpoints and their exact configuration destinations; Proxmox IP addresses are not assumed.

**TAFA App 0.3.22:** The Control Center now uses four accessible responsive tabs (Overview, Settings, Connections, Maintenance & help), a calmer navy/teal palette with light/dark variants, and more compact system status and connection cards. Existing settings and backend endpoints remain unchanged.

**TAFA 0.3.26 compatibility fix:** If HA Core is still running older integration code and a deleted Wyoming entry triggers `Previously mapped integration missing; review first`, TAFA retries the approved JSON import with the stale stored entry association cleared. Only this exact error triggers the retry. The permanent HA integration fix remains 0.4.12; restart HA Core to activate it. No worker changes are required.

**TAFA 0.3.27 / HA integration 0.4.13:** JSON imports assign the imported GPU or CPU device to its actual Wyoming STT role. A stale opposite role is cleared only when it points to exactly the same entity; legitimate distinct providers are kept. The HA integration no longer automatically treats the only GPU provider as the CPU fallback. For a distinct external CPU fallback, also import the Proxmox speech server JSON. Restart HA Core after updating the integration.

**TAFA 0.3.28:** Approved JSON imports now reconcile stale CPU/GPU Wyoming duplicates inside the final Supervisor settings write, using a freshly reloaded options snapshot. This fixes conflicts introduced between preview, HA registration, and saving, without changing distinct providers. Manual settings still reject duplicates; only user-approved worker/CT imports can clean the exact opposite-role alias.

## TAFA Dashboard (App 0.3.29 / integration 0.4.14)

TAFA Dashboard is now the default HA integration sidebar panel, based on the portable TAFA Home design rather than copying private household-specific Kiosk scripts. It offers configurable lights, solar and energy, batteries, EV, heating, heat pumps, fuel, appliances, cameras, weather, waste, shopping and Assist. HA administrators manage visible modules and select entity bindings in **Configure dashboard**; Home Assistant persists them for all users and tablets. The prior Voice Center remains accessible as **Voice services**, with device controls and announcements intact. No user automations or legacy Jarvis resources are changed.

**TAFA 0.3.30 / integration 0.4.15:** A dashboard-only option in the HA config flow supports first installing the portable dashboard even when the Piper backend is not yet reachable. Home Assistant stores its entity bindings centrally. Normal voice-enabled setup still checks Piper /health and can be completed later through approved Proxmox/GPU JSON imports.

**TAFA 0.3.31 / integration 0.4.16:** The built-in TAFA Dashboard and editor use distinct web component names from a separately installed `tafa-home-dashboard` Lovelace preview, preventing a registration collision when both are opened in the same browser session.


**TAFA App 0.3.32 / integration 0.4.17:** No duplicate top toolbar on the integrated dashboard home view. The native bottom TAFA navigation opens Voice services; the native settings gear opens admin-only HA-persisted dashboard configuration. Contextual Back/Save/Cancel actions only appear while inside a subview.


**TAFA App 0.3.33 / integration 0.4.18:** The TAFA entry in the native dashboard navigation now renders voice service management in place, retaining dashboard navigation and visual styling. Status, devices, Alexa announcements, sources and learning use the same card and accent system. A standalone voice view remains available at `/tablet_assist_for_alexa?view=voice`. No automation migration is required.
