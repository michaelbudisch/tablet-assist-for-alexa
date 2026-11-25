# Jarvis GPU Worker 2.2.4

**English** | [Deutsch](README.de.md) · [Project overview](../README.md)

## Token-free Windows setup

Run **00-Konfiguration.bat** to create `.env` with LAN address and model defaults only; **01-Installieren.bat** builds/starts GPU Whisper and Qwen Stream; **02-Starten.bat** starts them, **03-Neustarten.bat** restarts active worker containers, and **04-Verbindungsdaten.bat** generates a token-free IP/port TXT for Home Assistant. `Setup.ps1` remains a compatible entry point. Existing `.env` and Docker volumes are preserved. Android app and private dashboard are not changed.

**Security:** Extra TAFA worker API keys are no longer required. Bind services to your private `LAN_IP` and restrict inbound Windows firewall traffic to Home Assistant and the speech server. No public port forwarding, guest Wi-Fi access or proxying of the generator/control routes. A public HTTPS audio proxy must only serve short-lived opaque MP3 GET URLs.



## 2.2.4 — TAFA JSON import

`04-Verbindungsdaten.bat` now generates **`tafa-worker.json`** rather than a text walkthrough. The manifest contains a stable local worker identity, current private IP, and only running Wyoming Whisper, Qwen TTS and optional Ollama endpoints. Import it in TAFA Control Center > Settings; reimport after an IP change uses the same identity. Models must be already installed and selected before Ollama conversation-agent provisioning. No API secrets, model changes or extra router ports.

## 2.2.3 — Compact endpoint TXT

**New:** `GPU-Worker-Verbindungsdaten.txt` now lists only GPU PC URLs/IPs for Wyoming Whisper (10300), Qwen TTS (10502) and optional Ollama (11434), with the exact Home Assistant or TAFA destination for each value in DE/EN. No onboarding wall of text or invented Proxmox IPs. TAFA 0.3.21 adds connection status beside configured addresses and last actual STT route.

## 2.2.2 — Generated connection TXT includes full Home Assistant onboarding

**New:** `04-Verbindungsdaten.bat` creates `GPU-Worker-Verbindungsdaten.txt` from your existing `.env` / `LAN_IP` and opens it in Notepad. The TXT contains full **German and English** guidance from first setup to a real spoken test; no API tokens or credentials. It is also generated during Prepare, Install and Start. Report generation does not start any Docker services.

| Service | Home Assistant integration | TAFA App Configuration |
|---|---|---|
| **GPU Whisper** `GPU-IP:10300` | Add **Wyoming Protocol** under Devices & services (GPU LAN host and TCP port 10300); find the actual new `stt.*` entity ID | `gpu_stt` = GPU entity, `gpu_stt_host` = bare GPU IP |
| **CPU Whisper** `PROXMOX-IP:10300` | Add a **separate Wyoming Protocol** integration for the CPU speech server; use its actual STT entity | `cpu_stt` = CPU entity, different from GPU STT |
| **Qwen streaming TTS** `http://GPU-IP:10502` | Choose **Tablet Assist Stream** as TTS in the Assist pipeline | `gpu_base` = full URL, `hardware_profile=automatic` |
| **Ollama text inference** `http://GPU-IP:11434` | Add **Ollama** integration and a conversation agent using an installed text model such as `qwen3:4b-instruct`; copy the real `conversation.*` ID | `llm_agent` = Ollama HA entity ID, **not** device name |

**Important:** Supplying the Qwen GPU URL alone **does not enable GPU Whisper**. Wyoming Protocol creates the HA STT entity required by `gpu_stt`. TAFA can auto-select one Wyoming STT provider; with CPU and GPU, explicitly set both distinct entity IDs. External Proxmox requires `speech_mode=external` and `external_piper_base=http://PROXMOX-IP:5000`; the GPU worker cannot infer the separate CPU server IP.

The **TAFA Lokal** Assist pipeline should use **Tablet Assist Sprachrouter** for STT (GPU to CPU fallback), **Tablet Assist Gespraechsrouter** for conversation (Ollama), and **Tablet Assist Stream** for TTS (Qwen to Piper fallback). After a question, `letztes_backend=zusatzrechner` means GPU recognition and `homeserver` CPU/fallback. Android's ~1700 ms end-of-speech pause and Ollama response time are separate.

Default worker BAT install does **not** launch Ollama. Optionally run `docker compose --profile llm up -d ollama ollama-gateway` and select or deliberately install a local text model. Never expose LAN API ports to the Internet.

## 2.2.1 — Structured production Ring sequence

New private-LAN `POST /describe/sequence` on the existing Vision service. Standard: 12 chronological JPEGs (768 px max edge); detail: 4 selected higher-resolution JPEGs (1024 px max edge). Both use a bounded internal 16384-token context and the same vision gate. JSON includes a concise German description, tri-state evidence (yes/no/uncertain), delivery_assessment (likely/uncertain/no_evidence) and timing. A clothing hint alone is uncertain. Invalid or contradictory model output is rejected or downgraded. This is not proof of delivery. Existing /describe, /detect and /benchmark/sequence remain compatible.

Preserve .env and model volumes. Rebuild only Vision: `docker compose --profile vision up -d --build --no-deps vision`. Verify capabilities and run `docker compose exec -T vision python -m unittest -v test_server test_sequence_benchmark test_priority_gate`. Do not install the older 1.6.1 HA overlay on an already customized live backend; HA integration of the structured endpoint is a separate step after deployment. No separate container or model download is required if Qwen3-VL is already installed.

### Home Assistant (backend 1.6.2)

Structured Ring analysis is included in the current integration. Install the complete integration or the CI overlay `jarvis-ring-backend-1.6.2` on a compatible 1.6.x installation. Tablet single-image analysis is unchanged. `describe_camera` with `mode: ring_video` uses twelve frames, with four high-resolution detail frames for uncertain delivery evidence and compatibility fallbacks. Production no longer schedules A/B tests. See [Ring delivery hints](../homeassistant/examples/RING.md) for an example configuration.

## 2.0.0 — operations-ready update (compatible defaults)

The worker now has an optional **read-only diagnostics profile** at private-LAN
port **10504**. Start it with `docker compose --profile ops up -d --build ops`;
query private-LAN `GET /health`, `GET /status` or `GET /selftest` without a key. The endpoint checks whether configured
services are reachable and reports GPU statistics only when `nvidia-smi` is
available in the container. It **does not** run speech recognition, synthesis,
or inference in the background. Inactive Compose profiles show as unavailable.

**Vision scheduling:** optional `priority: "interactive" | "background"` and
`wait_ms: 0..20000` on `/describe` and `/detect`. Default is immediate
busy response (compatible with existing Home Assistant clients). The queue
is limited to six waiters and affects **only vision requests in that one
container**, not Whisper, TTS, or separate Ollama chats. `GET /capabilities`
advertises the available interface.

**Streaming TTS:** deterministic text cleanup is enabled by default
(`STREAM_TEXT_CLEANUP=1`); optional `STREAM_PRONUNCIATION` JSON dictionary,
e.g. `{"kWh":"Kilowattstunden"}`, and opt-in
`STREAM_SPEECH_SPLIT=1` for long replies. Private-LAN `POST /cancel`
requests cooperative interruption between synthesized audio chunks; clients
must stop playback locally too. Existing `/stream` and `/synthesize`
requests remain supported.

**Whisper diagnostics:** `python tools/check_audio.py recording.wav`
checks a local 16-bit PCM WAV for silence, clipping and too-short samples,
without uploading or storing the recording. Wyoming Whisper's VAD and
microphone end-of-speech settings are still controlled by the client/HA
pipeline; this is not an automatic VAD replacement.

**Release gate:** run `python check_release.py` (or
`python check_release.py --package ../jarvis-gpu-worker-2.0.0.zip`)
and all unit tests before deployment. Archive generation uses a file
allowlist and excludes `.env`, keys, sample recordings, caches and ZIPs.
Do **not** commit your real `.env`; keep existing model volumes.
Run `docker compose --profile vision --profile stream --profile ops config --quiet`
then rebuild only the services you use.

**Limits:** This release does not magically coordinate GPU scheduling across
all independent Docker containers, and continuous audio playback cancellation
depends on the connected client. Real RTX/Whisper/Qwen-TTS integration must
still be checked on the GPU machine after deployment.



> **Worker 1.9.0 schema update:** The local `/detect` response adds `genders` with coarse, fallible apparent presentation categories `man`, `woman`, `unknown`. This is not actual gender or identity recognition. Keep existing `.env` and model volumes; rebuild vision and update the HA backend together. [HA automations](../docs/en/ha-automations.md).

The existing optional vision container now also supports opt-in structured motion detections for the Echo Relay Lovelace controller. [Proactive setup](../docs/en/echo-relay-dashboard.md#motion-triggered-actions). No additional container or model is needed.

Optional GPU acceleration for TAFA. For complete installation instructions, supported ports, security and HA setup, see the [English worker guide](../docs/en/worker.md).

## New installation

Install Docker and NVIDIA GPU support. On Windows use Docker Desktop with WSL2; on Linux use Docker Engine, Compose and NVIDIA Container Toolkit. Run Setup.ps1 or setup-linux.sh in this directory. Preserve an existing .env file. Keep private LAN addresses and configuration safe. Models and images download on first build/start; allow sufficient SSD and GPU memory.

```bash
docker compose config --quiet
docker compose up -d --build whisper
docker compose --profile stream up -d --build qwen-stream
```

The Wyoming service uses port 10300; streaming TTS uses 10502. Only allow the necessary internal HA and CPU speech server clients. Do not forward these ports through your router. The optional older TTS profile on port 10501 is a separate model; do not run both TTS profiles simultaneously. Native CPU fallback remains available.


## Optional vision (1.8.0)

The optional `vision` profile uses the existing private Ollama for explicitly requested single-image descriptions. Existing text, Whisper, TTS and volumes are unchanged. Default `qwen3-vl:4b-instruct` (Ollama >= 0.12.7); alternatives `qwen3-vl:2b-instruct`, `qwen3-vl:8b-instruct`, `gemma3:4b`. Preserve .env; run on the GPU computer, not Proxmox.

```powershell
docker compose config --quiet
docker compose --profile llm --profile vision up -d --build vision
docker compose exec ollama ollama pull qwen3-vl:4b-instruct
docker compose exec vision python -m unittest -v test_server
```

Test a non-private image you may use with `.\Test-Vision.ps1 -ImagePath C:\Bilder\test.png`. Pull alternatives locally, set VISION_MODEL in .env and recreate only vision. Ollama limits loaded models to one; vision unloads after inference. Check actual shared VRAM and model-switch latency.

GET `/health` and POST `/describe` on private LAN port 10503 without an API key. JSON `{"image":"<raw base64 JPEG/PNG>","mode":"scene"}`, modes scene, objects, object_in_hand; optional model from the four tags. Max 2 MiB/12 MP, resized to 1280 px, image metadata removed. Response description, model, mode, limitation. No URL/stream fetching, arbitrary prompts, device tools, identity recognition, face matching or persistent image storage. Generic descriptions of visible people, clothes and carried objects are supported. Restrict firewall to HA, no public forwarding; HTTP is unencrypted. HA camera selection and Android camera delivery are available through the Echo Relay integration. Descriptions may be inaccurate. Stop only vision to disable without changing speech or volumes.

## Voice variants (1.5.0)

Keep the configured STREAM_VOICE_STYLE and existing fixed voice in .env. In fixed voice mode, one synthetic reference per variant is stored in qwen-data. Requests select an already prepared variant 1–9 via the validated voice_variant field. If the requested variant is missing, the existing default is used and reported in response headers. No remote voice uploads or model reloads are needed. Identical HA responses may be cached.

Prepare additional variants locally:

```bash
docker compose --profile stream stop qwen-stream
docker compose --profile stream run --rm --no-deps qwen-stream python /app/prepare_variants.py 2 3
docker compose --profile stream up -d --no-deps qwen-stream
```

If preparation fails, restart the streaming service. Do not delete volumes. Voice references are synthetic, not third-party recordings.

## Fixed voices (1.4.0)

Retain .env and set STREAM_VOICE_MODE=fixed, preserving STREAM_VOICE_STYLE. STREAM_VOICE_VARIANT defaults to 1. STREAM_FIXED_MODEL_SIZE defaults to 1.7B; 0.6B may reduce VRAM usage. A one-time design subprocess creates the synthetic reference and exits before Base inference starts. Existing models and voices remain in the volume. A new style or variant can create another reference. Prosody can still vary. Rebuild only the streaming container:

```bash
docker compose --profile stream up -d --build --no-deps qwen-stream
docker compose --profile stream logs -f qwen-stream
```

If VRAM is insufficient, try the smaller Base model or revert to fast/design mode and rebuild. No volumes need deletion.

## Optional Ollama (1.3.0)

```bash
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
docker compose exec ollama ollama ps
nvidia-smi
```

Ollama and speech models share GPU memory. Use the LAN-only gateway on port 11434 and the HA Ollama integration. Restrict firewall access to HA. Limit access to HA. Pull models locally through Docker; no model-management endpoints are exposed. Start with short responses, context 4096, history 6, model unload-on-idle and no extra AI tools; test before selecting the LLM as a conversation agent. Stop the two llm services to revert without deleting volumes. Local intents can work when the GPU host is offline.

## Earlier modes and compatibility

The fast, styled and design streaming profiles from 1.2.0 remain available. The fast profile uses the smaller model. The original non-streaming TTS service and the 1.1.x experimental streaming service are alternatives. Version 1.1.1 pinned Transformers and qwen-tts-hf to address an encoder compatibility issue; version 1.0.1 used Compose GPU reservations. Do not install the old standalone worker/proxmox TTS router alongside the current CPU server installer.

## Testing

Use Test-Stream.ps1 for latency, Test-Voice.ps1 to listen to locally generated audio, or Test-Qwen.ps1 for the older non-streaming service. First requests may include CUDA warm-up. Test CPU fallback with the GPU unavailable, voice changes and Bluetooth playback. GPU inference and device compatibility require real hardware validation.

[Worker changelog](CHANGELOG.md) · [Main repository](../README.md)


## Jarvis model settings (1.8.0)

With Jarvis Tablet Audio 1.5.0, the dashboard's **AI models and performance** panel selects installed text and vision models and a matching context (2048/4096/8192 tokens) and residency (0/60/120/300/600 seconds). Selecting `qwen3-vl:4b-instruct` for both avoids alternating model weights; verify real VRAM peaks alongside Whisper and TTS. Ollama still permits one loaded model and one parallel request. No automatic downloads, new service, public Ollama endpoint or volume changes are added. Legacy vision callers retain immediate unload by default.

The LAN-only `GET /runtime` reports only allowlisted installed/loaded models. `POST /describe` additionally accepts bounded `keep_alive` and `num_ctx` and reports inference timing metrics. The HA integration supplies saved parameters; its existing Ollama conversation agent receives matching settings through native config-subentry persistence, preserving prompts, tools and history. Restrict unauthenticated worker HTTP endpoints to trusted HA addresses with the host firewall. Camera-display commands still bypass both inference models. Settings changes apply on the next request; the first request after idle/restart may load the model.
