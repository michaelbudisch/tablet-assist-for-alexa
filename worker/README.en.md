# Jarvis GPU Worker 1.5.0

**English** | [Deutsch](README.md)

Optional GPU acceleration for Tablet Assist for Alexa. For complete installation instructions, supported ports, security and HA setup, see the [English worker guide](../docs/en/worker.md).

## New installation

Install Docker and NVIDIA GPU support. On Windows use Docker Desktop with WSL2; on Linux use Docker Engine, Compose and NVIDIA Container Toolkit. Run Setup.ps1 or setup-linux.sh in this directory. Preserve an existing .env file. Keep tokens and LAN addresses private. Models and images download on first build/start; allow sufficient SSD and GPU memory.

```bash
docker compose config --quiet
docker compose up -d --build whisper
docker compose --profile stream up -d --build qwen-stream
```

The Wyoming service uses port 10300; streaming TTS uses 10502. Only allow the necessary internal HA and CPU speech server clients. Do not forward these ports through your router. The optional older TTS profile on port 10501 is a separate model; do not run both TTS profiles simultaneously. Native CPU fallback remains available.

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

[Worker changelog](CHANGELOG.md) · [German changelog](CHANGELOG.de.md) · [Main repository](../README.md)
