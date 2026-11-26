# TAFA integration through Marketplace (without TAFA App)

[Deutsch](../marketplace.md) · [Project](../../README.md) · [Recommended App installation](app.md)

**Alternative path:** Marketplace installs the HA integration `tablet_assist_for_alexa`, **not** the TAFA Home Assistant App with its built-in CPU Piper/Whisper engines and standalone Control Center. On HA OS, the [App setup](setup-guide.md) is usually the easier first-install option. **Never let both Marketplace and TAFA App manage the same integration.**

## Requirements

- Home Assistant Core **2026.11+**, compatible platform; back up your configuration.
- A compatible **external CPU speech server**, with Piper HTTP and Wyoming Whisper (such as [TAFA Proxmox](proxmox.md)).
- The signed [TAFA Device Bridge](../../android/README.md) for native microphone and Bluetooth media playback.
- Optional [GPU worker](worker.md), HA Ollama conversation agent and Alexa MP3 announcements.

Marketplace provides the unified TAFA integration. New installations do **not** need separate Jarvis Tablet Audio or Jarvis Speech Router. TAFA integration/dashboard functionality is part of this integration, while the TAFA App's **Control Center and bundled CPU processes** are **not** included in this route.

## Installation

1. Under **Settings → Marketplace → Add from link**, use `https://github.com/michaelbudisch/tablet-assist-for-alexa` with category **Integration**.
2. Install **TAFA**, restart HA Core and add/configure **TAFA** under **Devices & services**.
3. Enter the **external CPU Piper** origin, e.g. `http://CPU-SERVER:5000`.
4. In **HA → Devices & services**, add **Wyoming Protocol** with the CPU server on TCP **10300** and select the resulting `stt.*` entity in TAFA integration options. Piper HTTP alone does not provide Wyoming recognition.
5. Under **Settings → Voice assistants**, create/check **TAFA Lokal** with **Tablet Assist Sprachrouter**, **Tablet Assist Gespraechsrouter** and **Tablet Assist Stream**.
6. Optionally add GPU/Ollama entities in HA. Install Device Bridge, connect a Bluetooth speaker, then test a live request.

[Open Marketplace repository](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration) · [Start integration setup](https://my.home-assistant.io/redirect/config_flow_start/?domain=tablet_assist_for_alexa)

## CPU/GPU, updates and security

**CPU fallback:** Provide a working external CPU Wyoming STT entity and Piper when GPU Whisper/Qwen are unavailable. GPU TTS, GPU STT and Ollama are separate services. An offline GPU Ollama has **no automatically configured CPU LLM fallback**. Local HA intents can remain available without a text LLM.

Update this integration **only via Marketplace** when installed that way; avoid simultaneous TAFA App management. Do not delete an existing `jarvis_tablet_audio` legacy setup or automations without a separate migration check. Never expose worker ports publicly. See [security](security.md).

**Versions:** Use `custom_components/tablet_assist_for_alexa/manifest.json` for the repository integration version; the App is versioned separately. Physical installation and playback still require validation on each device.
