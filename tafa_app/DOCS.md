# TAFA App – maintainer notes and setup reference

[App install (EN)](../docs/en/app.md) · [App installieren (DE)](../docs/app.md) · [First-time setup](../docs/en/setup-guide.md)

This file points to the **current** installer workflow instead of accumulating outdated per-release onboarding steps. Historical changes are in [`CHANGELOG.md`](CHANGELOG.md). The App version is in [`config.yaml`](config.yaml); the bundled HA integration version is in [`bundle/tablet_assist_for_alexa/manifest.json`](bundle/tablet_assist_for_alexa/manifest.json).

## Setup contract

1. On HA OS 2026.11+, install TAFA from the repository in **Settings → Apps**; back up the HA configuration first.
2. Fresh installations have **`speech_mode=setup`**. Choose **local** for bundled CPU Piper/Faster-Whisper or **external** for a compatible CPU speech host. An installation in setup mode does **not** download CPU models.
3. The control panel is structured as **Overview → Connections → Settings → Devices & Multiroom → Maintenance & Help**, with a separate **Speak now** browser test. All addresses and Wyoming/Ollama entity selections belong under **Connections**. Optional **Quick setup via JSON** imports only GPU worker endpoints.
4. External CPU mode requires Piper HTTP and HA **Wyoming Protocol** at **CPU-IP:10300**; select the resulting CPU `stt.*` entity. GPU Wyoming is an **additional separate integration**. Qwen URL alone does not activate GPU Whisper.
5. HA Core must restart once when TAFA first stages or updates the unified integration. Confirm **TAFA Lokal** with TAFA STT, conversation and streaming TTS entities. Existing pipelines and custom automations are preserved.
6. Use the [signed Device Bridge](../android/README.md) and a dedicated non-admin HA account per tablet. Connect a room and start the native player. Test the wakeword/microphone route and Bluetooth output on the **physical tablet**.

## Diagnostics and limitations

- **TAFA → Speak now** is browser-only: HTTPS/localhost for microphone capture; the browser shows transcript, answer, router data and stage timings. Playback is browser output, **not** a native room/Echo playback test. Its transcript is local transient page state, not a stored long-term log.
- A **network probe** confirms reachability, not STT recognition, model readiness, Alexa MP3 retrieval or real speaker output. Validate each stage with actual audio.
- STT fallback can use configured **CPU Whisper** and TTS fallback **CPU Piper** if GPU workers are offline; this **does not** create a fallback **Ollama text model** automatically.
- Native Device Bridge owns microphone and camera permissions, and camera upload is explicitly enabled per room and started separately.
- Worker model endpoints without an extra TAFA API token require private-LAN firewall restrictions. HA sessions and access tokens are still necessary.

## Installation safety

The App stages just **`custom_components/tablet_assist_for_alexa`** and replaces only **its own verified unchanged files**, backing up earlier versions under `<HA config>/.tafa/rollback`. It does not edit `configuration.yaml`, HA `.storage`, old automations or independent Marketplace/HACS installations.

For advanced integration-only installation see [Marketplace](../docs/en/marketplace.md); never run Marketplace and App installation management at the same time. For older Jarvis-only setups see the [legacy migration reference](../docs/en/home-assistant.md). Complete hardware qualification must be done on each target HA/Android/GPU combination.
