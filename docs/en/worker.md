[Deutsch](../worker.md) | **English** · [Project overview](../../README.md)

# Optional AI computer — original GPU worker 1.5.0

The repository includes the original Jarvis GPU Worker 1.5.0. Models are not bundled; build and first startup download them separately. Windows requires Docker Desktop with WSL2 and NVIDIA drivers. Linux requires Docker Engine/Compose and NVIDIA Container Toolkit. Allow enough SSD space for models. Only trusted private-network access; never expose service ports publicly. Real GPU inference and Linux setup have not been tested end-to-end.

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

Streaming supports /health, /stream (24 kHz PCM s16le mono), and /synthesize. The former non-streaming profile tts uses port 10501; do not run both TTS models at once. Prepare voice variants locally; see [worker reference](../../worker/README.en.md).

Optional local LLM:

```bash
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
```

Ollama shares the GPU. Test services one at a time with limited VRAM. Use the authenticated Ollama interface via the HA integration, storing the key locally in its dialog. Models may compete for GPU memory. The CPU setup does not require an extra GPU computer.

## 3. Connect Home Assistant and CPU server

Add GPU Wyoming to HA using the host IP and TCP 10300. Select the entity and optional GPU streaming address/key in the Marketplace integration; in the legacy configuration template set gpu_stt, GPU host and API token. For MP3 announcements, set your actual local values in /etc/jarvis-local.env:

```ini
JARVIS_GPU_BASE=http://gpu.example.invalid:10502
JARVIS_TTS_TOKEN=REPLACE_WITH_WORKER_TOKEN
```

Keep the file root-only. Restart with `systemctl restart jarvis-mp3`. Select Automatic. Without a GPU or on failure before playback starts, Piper is the fallback. Do not additionally install the original worker/proxmox/tts_router.py reference alongside the main installer.

## 4. Test

On Windows run Test-Stream.ps1 and Test-Voice.ps1 from the worker folder. On Linux test /health, /synthesize and /stream with local values and credentials. Do not expose keys in screenshots, logs or source control. Test native Assist playback and MP3 with the GPU host turned off.
