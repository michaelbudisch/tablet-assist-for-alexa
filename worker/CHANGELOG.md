**English** | [Deutsch](CHANGELOG.de.md)

# 1.5.0

- Optional authenticated request field `voice_variant`: choose an existing synthetic reference 1–9 for the current voice description without restarting. Missing variants use the configured reference; response headers report the effective variant and status. No voice uploads or remote model reloads.
- Local `prepare_variants.py` command to create variants in the existing volume, with the streaming container stopped. Existing references are retained.
- No changes to LLM, STT, API key, port, or default voice. Static and stub-based checks; GPU / acoustic testing remains on target.

# 1.4.0

- Added `fixed` mode: create an original synthetic VoiceDesign reference once, save it in the existing persistent model volume, and reuse it for all subsequent streaming requests with Qwen Base.
- Separate one-time design subprocess releases VRAM before Base loads. The existing design, styled and fast modes remain available.
- Optional 0.6B Base model and voice variant; changing style or variant creates a new saved reference without deleting the old one.
- Stable API, token, LAN port and audio format; no changes to Whisper or Ollama. Static checks only; actual CUDA runtime and voice consistency still require testing.

# 1.3.0

- Optional Ollama GPU service (`llm` profile) with local-only inference, one loaded model, one parallel request, 4096-token default context and unload-on-idle default.
- Authenticated, LAN-bound streaming reverse proxy. Existing worker key; no direct Ollama host port or model-management endpoints exposed.
- Qwen3 4B Instruct installation and native HA Ollama setup instructions.
- Existing STT and TTS services, image tags and named volumes retained. Model installation and target GPU runtime still need testing.

# 1.2.0

- Optional streaming voice profiles: fast (0.6B), styled (1.7B), design (1.7B).
- Configurable voice description, unchanged authenticated API and PCM format.
- Test-Voice.ps1 generates and plays a WAV locally.
- Default remains the previously working fast profile; model runtime and VRAM for new profiles require testing.

# 1.1.1
- Pin Transformers 5.15.1 and qwen-tts-hf 0.1.1.post1 in the streaming image to avoid the upstream MimiModel encoder upsample property incompatibility.
- Check the pinned package versions during the image build.
- Preserve Whisper, original Qwen, model caches and existing .env.

# 1.1.0
- Optional Faster Qwen streaming service on LAN port 10502.
- Authenticated PCM stream and complete WAV endpoints.
- Existing Whisper and original Qwen unchanged.

# 1.0.1
- Use GPU device reservations instead of the Compose 2.30+ `gpus` key for both services.
- Preserve existing configuration and named volumes.

# 1.0.0
- Optional GPU Whisper via upstream Wyoming server, separate Qwen3-TTS service.
- Private LAN bindings, token-protected synthesis and local WAV test.
- Standalone Proxmox TTS fallback proxy, not enabled automatically.
