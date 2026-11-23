# Optional AI computer — GPU worker 1.9.0

**English** | [Deutsch](../worker.md) · [Project overview](../../README.md)

> **Worker 1.9.0 schema update:** The local `/detect` response adds `genders` with coarse, fallible apparent presentation categories `man`, `woman`, `unknown`. This is not actual gender or identity recognition. Keep existing `.env` and model volumes; rebuild vision and update the HA backend together. [HA automations](ha-automations.md).

The repository includes the Jarvis GPU Worker 1.9.0. Models are not bundled; build and first startup download them separately. Windows requires Docker Desktop with WSL2 and NVIDIA drivers. Linux requires Docker Engine/Compose and NVIDIA Container Toolkit. Allow enough SSD space for models. Only trusted private-network access; never expose service ports publicly. Real GPU inference and Linux setup have not been tested end-to-end.

## 1. Configuration

Windows PowerShell in the worker directory:

```powershell
.\Setup.ps1
```

Linux from worker:

```bash
bash setup-linux.sh
```

Both create a local .env with a random API token and preserve an existing .env. Never publish the key. Restrict port 10300 to HA, port 10502 to HA and the CPU speech server, and port 11434 (if using Ollama) to HA.

## 2. Start services

```bash
docker compose config --quiet
docker compose up -d --build whisper
docker compose --profile stream up -d --build qwen-stream
```

Streaming supports /health, /stream (24 kHz PCM s16le mono), and /synthesize. The former non-streaming profile tts uses port 10501; do not run both TTS models at once. Prepare voice variants locally; see [worker reference](../../worker/README.md).

Optional local LLM:

```bash
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
```

Ollama shares the GPU. Test services one at a time with limited VRAM. Use the authenticated Ollama interface via the HA integration, storing the key locally in its dialog. Models may compete for GPU memory. The CPU setup does not require an extra GPU computer.

## Optional: vision

The vision profile shares Ollama, port 10503 restricted to HA. [Setup and API](../../worker/README.md#optional-vision-180). HA camera selection is separate.

## 3. Connect Home Assistant and CPU server

Add GPU Wyoming to HA using the host IP and TCP 10300. Select the entity and optional GPU streaming address/key in the Marketplace integration; in the legacy configuration template set gpu_stt, GPU host and API token. For MP3 announcements, set your actual local values in /etc/jarvis-local.env:

```ini
JARVIS_GPU_BASE=http://gpu.example.invalid:10502
JARVIS_TTS_TOKEN=REPLACE_WITH_WORKER_TOKEN
```

Keep the file root-only. Restart with `systemctl restart jarvis-mp3`. Select Automatic. Without a GPU or on failure before playback starts, Piper is the fallback. Do not additionally install the original worker/proxmox/tts_router.py reference alongside the main installer.

## 4. Test

On Windows run Test-Stream.ps1 and Test-Voice.ps1 from the worker folder. On Linux test /health, /synthesize and /stream with local values and credentials. Do not expose keys in screenshots, logs or source control. Test native Assist playback and MP3 with the GPU host turned off.

## Jarvis model settings (1.8.0)

With Jarvis Tablet Audio 1.5.0, the dashboard's **AI models and performance** panel selects installed text and vision models and a matching context (2048/4096/8192 tokens) and residency (0/60/120/300/600 seconds). Selecting `qwen3-vl:4b-instruct` for both avoids alternating model weights; verify real VRAM peaks alongside Whisper and TTS. Ollama still permits one loaded model and one parallel request. No automatic downloads, new service, public Ollama endpoint or volume changes are added. Legacy vision callers retain immediate unload by default.

The authenticated `GET /runtime` reports only allowlisted installed/loaded models. `POST /describe` additionally accepts bounded `keep_alive` and `num_ctx` and reports inference timing metrics. The HA integration supplies saved parameters; its existing Ollama conversation agent receives matching settings through native config-subentry persistence, preserving prompts, tools and history. Browser clients never receive the worker key. Camera-display commands still bypass both inference models. Settings changes apply on the next request; the first request after idle/restart may load the model.
