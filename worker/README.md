# Jarvis GPU Worker 2.1.0

 
## 2.1.0 — Optional Ring multi-frame A/B benchmark

This is **opt-in** and does not change the existing /describe, /detect, Home Assistant Ring automation, MP3 announcements or infoboxes. Authenticated `POST /benchmark/sequence` on private vision port 10503 compares four **independent** image descriptions with 4, 8 or 12 **joint** images in one Ollama Qwen3-VL request. Each frame must have an increasing `second` timestamp and a base64 JPEG/PNG `image`. The endpoint returns model responses, preparation time, inference time and Ollama timings; it neither downloads Ring footage nor archives images. It does **not** accept MP4 directly.

On the GPU machine, after updating the worker source while preserving your existing .env and volumes:

```bash
docker compose --profile vision up -d --build --no-deps vision
docker compose exec vision python -m unittest -v test_server test_sequence_benchmark test_priority_gate
```

For an **explicitly exported, authorized local Ring MP4**, install FFmpeg/FFprobe on the computer running the benchmark and run:

```powershell
python tools/benchmark_ring_video.py "C:\Videos\Ring-Test.mp4" --env-file .env --output ring-ab-results.json
```

By default the script targets `http://127.0.0.1:10503`; use `--base-url http://YOUR_PRIVATE_GPU_IP:10503` only on a trusted LAN. No video or image data are included in the local JSON results file, only model descriptions and timings. Do not send recordings or the worker token to public hosts. Inference for 12 frames may run out of context or GPU memory; a failed test leaves the production path unchanged. For a fair A/B test, use the **same** sample video, model and 4096-token context first; compare quality and timing. Because frames are sampled, this is *not* native MP4/video-token inference.


**English** | [Deutsch](README.de.md) · [Project overview](../README.md)

## 2.0.0 — operations-ready update (compatible defaults)

The worker now has an optional **read-only diagnostics profile** at private-LAN
port **10504**. Start it with `docker compose --profile ops up -d --build ops`;
query authenticated `GET /health`, `GET /status` or `GET /selftest` using
`X-API-Key: <existing JARVIS_TTS_TOKEN>`. The endpoint checks whether configured
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
`STREAM_SPEECH_SPLIT=1` for long replies. Authenticated `POST /cancel`
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

Install Docker and NVIDIA GPU support. On Windows use Docker Desktop with WSL2; on Linux use Docker Engine, Compose and NVIDIA Container Toolkit. Run Setup.ps1 or setup-linux.sh in this directory. Preserve an existing .env file. Keep tokens and LAN addresses private. Models and images download on first build/start; allow sufficient SSD and GPU memory.

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

Authenticated GET `/health`, POST `/describe` on private LAN port 10503 with existing X-API-Key. JSON `{"image":"<raw base64 JPEG/PNG>","mode":"scene"}`, modes scene, objects, object_in_hand; optional model from the four tags. Max 2 MiB/12 MP, resized to 1280 px, image metadata removed. Response description, model, mode, limitation. No URL/stream fetching, arbitrary prompts, device tools, identity recognition, face matching or persistent image storage. Generic descriptions of visible people, clothes and carried objects are supported. Restrict firewall to HA, no public forwarding; HTTP is unencrypted. HA camera selection and Android camera delivery are available through the Echo Relay integration. Descriptions may be inaccurate. Stop only vision to disable without changing speech or volumes.

## Voice variants (1.5.0)

Keep the configured STREAM_VOICE_STYLE and existing fixed voice in .env. In fixed voice mode, one synthetic reference per variant is stored in qwen-data. Requests select an already prepared variant 1–9 via the authenticated voice_variant field. If the requested variant is missing, the existing default is used and reported in response headers. No remote voice uploads or model reloads are needed. Identical HA responses may be cached.

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

Ollama and speech models share GPU memory. Use the authenticated gateway on private port 11434, the existing worker token and the HA Ollama integration. Limit access to HA. Pull models locally through Docker; no model-management endpoints are exposed. Start with short responses, context 4096, history 6, model unload-on-idle and no extra AI tools; test before selecting the LLM as a conversation agent. Stop the two llm services to revert without deleting volumes. Local intents can work when the GPU host is offline.

## Earlier modes and compatibility

The fast, styled and design streaming profiles from 1.2.0 remain available. The fast profile uses the smaller model. The original non-streaming TTS service and the 1.1.x experimental streaming service are alternatives. Version 1.1.1 pinned Transformers and qwen-tts-hf to address an encoder compatibility issue; version 1.0.1 used Compose GPU reservations. Do not install the old standalone worker/proxmox TTS router alongside the current CPU server installer.

## Testing

Use Test-Stream.ps1 for latency, Test-Voice.ps1 to listen to locally generated audio, or Test-Qwen.ps1 for the older non-streaming service. First requests may include CUDA warm-up. Test CPU fallback with the GPU unavailable, voice changes and Bluetooth playback. GPU inference and device compatibility require real hardware validation.

[Worker changelog](CHANGELOG.md) · [Main repository](../README.md)


## Jarvis model settings (1.8.0)

With Jarvis Tablet Audio 1.5.0, the dashboard's **AI models and performance** panel selects installed text and vision models and a matching context (2048/4096/8192 tokens) and residency (0/60/120/300/600 seconds). Selecting `qwen3-vl:4b-instruct` for both avoids alternating model weights; verify real VRAM peaks alongside Whisper and TTS. Ollama still permits one loaded model and one parallel request. No automatic downloads, new service, public Ollama endpoint or volume changes are added. Legacy vision callers retain immediate unload by default.

The authenticated `GET /runtime` reports only allowlisted installed/loaded models. `POST /describe` additionally accepts bounded `keep_alive` and `num_ctx` and reports inference timing metrics. The HA integration supplies saved parameters; its existing Ollama conversation agent receives matching settings through native config-subentry persistence, preserving prompts, tools and history. Browser clients never receive the worker key. Camera-display commands still bypass both inference models. Settings changes apply on the next request; the first request after idle/restart may load the model.
