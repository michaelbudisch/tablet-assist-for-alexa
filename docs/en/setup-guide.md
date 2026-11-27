# Set up TAFA – step by step

[Deutsch](../setup-guide.md) · [Project overview](../../README.md) · [App guide](app.md)

This guide is for **fresh installations**. The TAFA Home Assistant App includes the Control Center and can run CPU speech services. A separate Proxmox server, GPU worker, Ollama and internet-facing Alexa MP3 announcements are **optional**. Older Jarvis integrations and legacy API tokens are **not** needed; see [legacy migration](home-assistant.md).

## 1. Install TAFA in Home Assistant

Requirements: Home Assistant OS **2026.11 or later**, with **Apps** on `amd64` or `aarch64`; Android 9+ for Device Bridge. Back up HA before starting.

1. Under **Settings → Apps → Install app → Repositories**, add `https://github.com/michaelbudisch/tablet-assist-for-alexa`, install **TAFA** and start it.
2. Open **Apps → TAFA → User interface**. Fresh installations start with `speech_mode=setup`; CPU models are **not downloaded yet**. Choose **Local** or **External** speech mode deliberately under **Settings**.
3. TAFA stages a single HA integration, `tablet_assist_for_alexa`. **Restart Home Assistant Core once** after first install or a backend update, then restart the TAFA App if needed. Do not also install the Marketplace-managed copy.
4. Verify the **TAFA** integration under **Settings → Devices & services** and the **TAFA Lokal** Assist pipeline under **Settings → Voice assistants**. If the pipeline was not created, set it up with **Tablet Assist Sprachrouter** (STT), **Tablet Assist Gespraechsrouter** (conversation) and **Tablet Assist Stream** (TTS). Existing pipelines remain untouched.

The Control Center has **Overview**, **Connections**, **Settings**, **Devices & Multiroom**, **Maintenance & Help**, plus the separate **Speak now** entry. **Connections** manages addresses, CPU/GPU Wyoming entities, the Ollama agent and JSON import. **Settings** manages speech mode, voices and behavior.

## 2. Configure CPU speech recognition and voice

Choose **one** CPU setup:

| Mode | Requirements | Steps |
| --- | --- | --- |
| **TAFA Local** | Enough RAM and disk for the bundled Piper and Faster-Whisper engines | Choose **Settings → Speech mode: Local**, save and restart TAFA; allow the initial model download and check readiness. |
| **External CPU server** | A Debian/Proxmox host providing Piper HTTP and Wyoming Whisper | Install the [CPU speech server](proxmox.md), choose **Speech mode: External**, and set `http://CPU-SERVER:5000` as Piper in **Connections**. |

**For external CPU Whisper:** In **HA → Settings → Devices & services → Add integration → Wyoming Protocol**, connect to the CPU host on TCP **10300**. Select the resulting **actual** `stt.*` entity under **TAFA → Connections → CPU fallback**. Piper HTTP port 5000 is **not** the STT endpoint. Keep CPU and GPU Wyoming entities distinct.

Local mode uses TAFA's bundled CPU engines without Proxmox. The CPU fallback covers **Whisper STT and Piper TTS**; it does **not automatically provide a CPU Ollama language model**.

## 3. Optional GPU worker and local AI

On Windows use Docker Desktop with WSL2 and suitable NVIDIA drivers; on Linux use Docker Engine/Compose and NVIDIA Container Toolkit. Follow the [GPU worker guide](worker.md). From `worker/` on Windows:

1. Run `01-Installieren.bat` (or `00-Konfiguration.bat` beforehand). In addition to GPU Whisper and Qwen voice, this installs **only the `qwen3-vl:4b-instruct` Ollama model for both text and vision** and preloads it with `keep_alive=-1`.
2. Run `04-Verbindungsdaten.bat`. It creates **`tafa-worker.json`** plus **`GPU-Worker-Verbindungsdaten.txt`**.
3. In **TAFA → Connections → Quick setup via JSON**, select the JSON, **check the configuration**, and confirm GPU URLs. The text report lists ports; the GPU export cannot know your separate CPU server address.
4. Add **Wyoming Protocol** in HA for **GPU-IP:10300**, then select the new GPU `stt.*` entity in **TAFA → Connections → GPU/AI**. The fast GPU availability check accepts a bare IP without scheme or port. A Qwen TTS URL alone **does not enable GPU Whisper**.
5. Add the HA **Ollama** integration at `http://GPU-IP:11434`; choose **`qwen3-vl:4b-instruct`** for the conversation agent, turn thinking off, set keep-alive to **-1 (indefinite)**, and select the resulting `conversation.*` entity in TAFA **Connections**. Qwen speech synthesis remains separate.

**Tablet Assist Stream** prefers Qwen via `http://GPU-IP:10502`, falling back to Piper if unavailable **before playback begins**. The **Tablet Assist Sprachrouter** can fall back from GPU Wyoming to configured CPU STT. Open-ended LLM responses may remain unavailable when the GPU PC is offline unless a separate CPU conversation agent has been configured.

## 4. Connect the Android tablet

1. Install the current signed [TAFA Device Bridge](../../android/README.md). Create a dedicated **non-admin Home Assistant account per tablet**, and keep its access credentials/token on that device.
2. In Device Bridge **Connect**, set the HA base URL (no dashboard path) and authenticate. Grant microphone permission explicitly.
3. Optionally pair the Echo in **Android Bluetooth settings** for media audio. Start **Settings → Echo & audio player**. TAFA does **not** listen through the Echo microphone.
4. Under **Settings → Wakeword**, install the local model, pick a wake word, and start listening. Native microphone modes are **Muted**, **Wake word**, and optional **Always on**, which can also react to background speech.
5. Pair the enrolled tablet with its HA room/user under **TAFA → Devices & Multiroom**; see [Multiroom](../../homeassistant/examples/MULTIROOM.md).

## 5. Test an entire request

1. Check required CPU/GPU connections under **TAFA → Connections**; a successful network probe is **not** a live speech test.
2. Verify the three TAFA routers in the **TAFA Lokal** Assist pipeline.
3. Use **TAFA → Speak now** in a browser over **HTTPS or localhost**, allow microphone access and inspect measured STT/conversation/TTS timing. This is a **browser diagnostic** and browser playback test, **not** an Echo or Android audio test.
4. Use **Speak now** on Device Bridge and then test the chosen wake word. To hear speech on Echo, keep the native player running and pair Echo via Bluetooth.
5. Test with the GPU worker available and stopped to verify CPU Whisper and Piper fallback; inspect the STT router's actual backend attributes.

If an expected `stt.*` or `conversation.*` entity is missing, create it **in HA** through the corresponding Wyoming/Ollama integration before selecting it in TAFA.

## 6. Optional features

- [Multiple tablets and rooms](../../homeassistant/examples/MULTIROOM.md)
- [Camera permissions and setup](../../android/docs/camera-preparation.md) – default off
- [Alexa MP3 announcements](proxmox.md) and [Nginx HTTPS](nginx-proxy.md) – internet-accessible HTTPS files are required **only** for this separate Alexa notification path, not conversational Bluetooth playback
- [Marketplace-only alternative](marketplace.md) – never manage the same integration simultaneously through Marketplace and TAFA App
- [Security](security.md) – never expose internal CPU/GPU service ports publicly; normal HA authentication remains required even where LAN worker APIs have no extra TAFA token

**Compatibility:** Check the installed App, HA integration and signed Device Bridge versions independently. Documentation checks do not replace hands-on first-install tests on every supported platform.
