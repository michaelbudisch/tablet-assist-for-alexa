# TAFA Home Assistant App

[English App guide](../docs/en/app.md) · [Deutsche App-Anleitung](../docs/app.md) · [Full setup](../docs/en/setup-guide.md) · [Project](../README.md)

TAFA contains a **Control Center**, the integrated `tablet_assist_for_alexa` Home Assistant backend, the portable TAFA dashboard and optional local CPU Piper/Faster-Whisper. The App version is defined in [`config.yaml`](config.yaml); the HA integration has its own version in [`manifest.json`](../custom_components/tablet_assist_for_alexa/manifest.json). Do not assume they are the same version.

## Fresh installation

1. Back up Home Assistant (Home Assistant OS 2026.11+, amd64/aarch64). Under **Settings → Apps → Install app → Repositories**, add `https://github.com/michaelbudisch/tablet-assist-for-alexa`, then install and start **TAFA**.
2. A new instance starts with `speech_mode=setup`; **no CPU models download until you choose** Local or External in **TAFA → Settings**. Local starts bundled CPU Piper/Faster-Whisper; External uses a separately configured CPU speech server.
3. In **TAFA → Connections**, enter CPU Piper and Wyoming settings for external mode; add **Wyoming Protocol** for external STT in **HA → Devices & services** (CPU host, port 10300) and select the resulting actual `stt.*` entity. Local mode uses TAFA's built-in CPU speech engines.
4. The App safely provisions **one** unified HA integration. **Restart HA Core once** after installation or a backend update, then restart TAFA as required. Check **TAFA Lokal** in **Settings → Voice assistants**: **Tablet Assist Sprachrouter** (STT), **Tablet Assist Gespraechsrouter** (conversation), **Tablet Assist Stream** (TTS).
5. Install the [signed Android Device Bridge](../android/README.md), connect with its dedicated non-admin HA user, assign an existing HA area in TAFA, pair Bluetooth/Echo if needed and test an actual question. Use [Devices & Multiroom](../homeassistant/examples/MULTIROOM.md) for multiple tablets.

## Control Center

- **Overview:** system and speech route status.
- **Connections:** **Quick setup via JSON**, GPU host/fast availability check, GPU Wyoming, Qwen and Ollama, **CPU fallback** Piper/Wyoming, optional Alexa MP3 URLs.
- **Settings:** local/external speech mode, voice and conversation behavior, optional features. Server/IP fields are in **Connections**, not Settings.
- **Devices & Multiroom:** assign each registered tablet once to an existing HA area; camera permissions and reset controls are under Advanced.
- **Maintenance & Help:** backend status, downloads and diagnostics.
- **Speak now:** independent browser microphone/text test with Muted/Wake word/Always on, transient transcript and stage timing. Browser microphone requires **HTTPS/localhost**; playback is **in the browser**, not automatically on Android/Echo.

The **native Android wakeword microphone** runs independently of the browser page; its mute/wake/always-on mode is controlled on the tablet and by its HA-backed settings. Browser timing and HTTP/TCP endpoint reachability do **not** prove actual Echo media playback.

## Updates and alternatives

The App updates only its **own unchanged managed integration**, preserving a rollback in `<HA config>/.tafa/rollback`. It never overwrites a manually or Marketplace-managed integration. Do **not** install or update the same backend through both Marketplace and App. Existing automations and private dashboards are not silently replaced. HA Core must restart after backend updates.

A separate [Proxmox CPU server](../docs/en/proxmox.md), [GPU worker](../docs/en/worker.md), [Ollama](../docs/en/setup-guide.md) and [Alexa MP3 HTTPS](../docs/en/proxmox.md) remain optional. CPU Whisper and Piper fallback do **not** automatically provide a CPU fallback for Ollama text AI.

**Security:** TAFA LAN worker endpoints need no additional TAFA API token, but HA access tokens and normal HA permissions are still required for tablet connections. Keep unauthenticated model endpoints on a restricted trusted LAN; never publish them as public services.
