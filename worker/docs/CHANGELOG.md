# GPU worker changelog

## 2.2.5

- Optional Ollama setup integrated into `01-Installieren.bat`; model download requires separate consent.
- `tafa-worker.json` and `GPU-Worker-Verbindungsdaten.txt` generated from the same service snapshot, including IP, ports and service status.
- Move setup/test scripts under `scripts/`, detailed guides/changelogs under `docs/`; update launchers, packaging and CI.
- Keep ports, JSON schema, model volumes and existing Home Assistant systems unchanged.

## 2.2.4

- Replace the verbose connection TXT with machine-readable `tafa-worker.json`. Save a stable worker ID across LAN IP changes and export only running Whisper/Qwen/Ollama endpoints. No credentials or model changes.


## 2.2.3

- Make `04-Verbindungsdaten.bat` generate a concise bilingual endpoint-to-field list, including Wyoming GPU 10300, Qwen TTS 10502 and optional Ollama 11434. Only known local GPU addresses are included; no long instructions or invented Proxmox IPs.
- Existing `.env`, models, volumes and network access remain unchanged; align the worker image metadata and tags.

## 2.2.2

- GPU-Worker connection report now includes a bilingual (DE/EN) **first-run Home Assistant integration checklist** with the detected GPU LAN IP and exact TAFA App field mappings, rather than ports alone.
- Explicitly explains adding **Wyoming Protocol** for GPU Whisper on TCP 10300, a separate CPU Wyoming STT for Proxmox fallback, and the **Ollama** HA integration for text AI. Makes clear that Qwen TTS at 10502 is not Whisper or Ollama.
- Shows where to find real `stt.*` and `conversation.*` entity IDs, how to assign `cpu_stt`, `gpu_stt`, `gpu_stt_host`, `gpu_base`, `llm_agent`, and how to check the router's `letztes_backend` after a spoken request.
- `04-Verbindungsdaten.bat` now opens the generated file in Notepad. Existing `.env`, models, ports, services and token-free LAN operation are unchanged.

## 2.2.1

- Removed extra TAFA API token checks from private-LAN Qwen, Vision, Diagnostics and Ollama endpoints. Home Assistant user authentication stays in place.
- Added one-click Windows BAT scripts for configuration, installation, start, restart and a token-free IP/port report.
- Setup.ps1 and setup-linux.sh create a token-free .env; existing .env and model volumes are preserved.
- Ports must remain on a trusted LAN with firewall allowlisting; never forward GPU/MP3 generator ports to the Internet.


 
## 2.2.0

- Added production structured sequence API with bounded 12-frame standard and 4-frame detail profiles, strict schema and conservative delivery evidence. Shared 16384 context; existing routes remain compatible. Added mocked contract tests; actual GPU quality and timing require deployment.

## 2.1.1

- Fix joint Qwen3-VL benchmark context overflow: use bounded internal context floors of 8192 tokens for four frames and 16384 for eight or twelve, leaving independent and production requests unchanged. Report requested and effective context in benchmark metrics. Offline tests verify all three sizes; real GPU memory and timing still require testing.

## 2.1.0

- Added opt-in private `/benchmark/sequence` endpoint for 4 independent frames versus 4/8/12 jointly described Qwen3-VL frames; production still-image endpoints and Ring automations are unchanged.
- Added local FFmpeg MP4 sampler with identical reference frames, per-mode latency measurements and optional redacted JSON report; no recording, images or keys are retained.
- Authentication, strict frame/timestamp/model/context bounds and shared vision admission gate apply; no external video URLs or native MP4 upload.
- Added offline tests, container build inclusion and documentation; real RTX/GPU timings require deployment and a locally authorized clip.


**English** | [Deutsch](CHANGELOG.de.md) · [Project overview](../../README.md)

## 2.0.0

- Added optional authenticated `ops` status/selftest service for Whisper TCP, TTS, Vision, Ollama, and GPU metrics when available; no stored private audio/video.
- Vision `/describe` and `/detect` support opt-in bounded priority queuing and `/capabilities`, retaining legacy immediate-busy defaults. Queue scope is vision only.
- Streaming Qwen TTS has deterministic text normalization, optional pronunciation mappings and sentence segmentation, plus cooperative `/cancel`.
- Local Whisper WAV silence/clipping/length diagnostics; no transcription data retention.
- GitHub CI, offline tests, Docker Compose validation and a secret-safe release ZIP builder.
- Preserved existing Ollama, TTS/Whisper and Home Assistant API behavior by default. Hardware-level smoke testing remains a deployment step.

## 1.9.0

### 1.9.0 — schema update

- Updated uploaded worker schema includes optional appearance-based categories; no identity or facial recognition. HA validator accepts legacy results as well.

- Authenticated `/detect` endpoint with a fixed validated people/dog schema and coarse adult/child/unknown appearance. No names, identity, gender, arbitrary prompts or model-chosen actions.
- Reuses the existing vision container, Ollama and selected model/context/residency. Fourteen isolated worker tests cover the new response validation and existing descriptions. HA opt-in, cooldown and playback coordination live in backend 1.6.0.

## 1.8.0

- Authenticated installed/loaded model status and bounded per-request residency/context for matching HA text/vision settings. Legacy immediate-unload defaults remain compatible; response timings support load-cost diagnosis. No additional service, model download, endpoint exposure or speech changes.

## 1.7.0

- Scene descriptions may include generic visible people, clothing and carried objects. No naming, face matching, sensitive-trait guesses or inference of movement/history from a still. Existing authenticated single-image API and fixed modes remain compatible.

## 1.6.0

- Optional authenticated single-image vision service sharing local Ollama; four allowed model tags, Qwen3-VL 4B Instruct default.
- Fixed description modes, size limits, metadata removal, one concurrent vision request, unload after inference. No capture or persistent image storage.
- Mock API tests and PowerShell client. Speech and text unchanged. GPU and HA camera integration require target tests.

## 1.5.0

- Optional authenticated request field `voice_variant`: choose an existing synthetic reference 1–9 for the current voice description without restarting. Missing variants use the configured reference; response headers report the effective variant and status. No voice uploads or remote model reloads.
- Local `prepare_variants.py` command to create variants in the existing volume, with the streaming container stopped. Existing references are retained.
- No changes to LLM, STT, API key, port, or default voice. Static and stub-based checks; GPU / acoustic testing remains on target.

## 1.4.0

- Added `fixed` mode: create an original synthetic VoiceDesign reference once, save it in the existing persistent model volume, and reuse it for all subsequent streaming requests with Qwen Base.
- Separate one-time design subprocess releases VRAM before Base loads. The existing design, styled and fast modes remain available.
- Optional 0.6B Base model and voice variant; changing style or variant creates a new saved reference without deleting the old one.
- Stable API, token, LAN port and audio format; no changes to Whisper or Ollama. Static checks only; actual CUDA runtime and voice consistency still require testing.

## 1.3.0

- Optional Ollama GPU service (`llm` profile) with local-only inference, one loaded model, one parallel request, 4096-token default context and unload-on-idle default.
- Authenticated, LAN-bound streaming reverse proxy. Existing worker key; no direct Ollama host port or model-management endpoints exposed.
- Qwen3 4B Instruct installation and native HA Ollama setup instructions.
- Existing STT and TTS services, image tags and named volumes retained. Model installation and target GPU runtime still need testing.

## 1.2.0

- Optional streaming voice profiles: fast (0.6B), styled (1.7B), design (1.7B).
- Configurable voice description, unchanged authenticated API and PCM format.
- Test-Voice.ps1 generates and plays a WAV locally.
- Default remains the previously working fast profile; model runtime and VRAM for new profiles require testing.

## 1.1.1
- Pin Transformers 5.15.1 and qwen-tts-hf 0.1.1.post1 in the streaming image to avoid the upstream MimiModel encoder upsample property incompatibility.
- Check the pinned package versions during the image build.
- Preserve Whisper, original Qwen, model caches and existing .env.

## 1.1.0
- Optional Faster Qwen streaming service on LAN port 10502.
- Authenticated PCM stream and complete WAV endpoints.
- Existing Whisper and original Qwen unchanged.

## 1.0.1
- Use GPU device reservations instead of the Compose 2.30+ `gpus` key for both services.
- Preserve existing configuration and named volumes.

## 1.0.0
- Optional GPU Whisper via upstream Wyoming server, separate Qwen3-TTS service.
- Private LAN bindings, token-protected synthesis and local WAV test.
- Standalone Proxmox TTS fallback proxy, not enabled automatically.
