# Optional AI computer — GPU worker 2.2.2

**English** | [Deutsch](../worker.md) · [Project overview](../../README.md)

> **Worker 1.9.0 schema update:** The local `/detect` response adds `genders` with coarse, fallible apparent presentation categories `man`, `woman`, `unknown`. This is not actual gender or identity recognition. Keep existing `.env` and model volumes; rebuild vision and update the HA backend together. [HA automations](ha-automations.md).

The repository includes TAFA GPU Worker 2.2.5, with token-free LAN APIs and an easier Windows setup. Models are not bundled; build and first startup download them separately. Windows requires Docker Desktop with WSL2 and NVIDIA drivers. Linux requires Docker Engine/Compose and NVIDIA Container Toolkit. Allow enough SSD space for models. Only trusted private-network access; never expose service ports publicly. Real GPU inference and Linux setup have not been tested end-to-end.

**New 2.2.5:** `01-Installieren.bat` optionally configures Ollama (separate approval for downloading the model). `04-Verbindungsdaten.bat` writes the TAFA JSON import plus an address TXT. **CPU Whisper** uses Wyoming Protocol; **Piper** supplies CPU TTS fallback. [Quick start](../../worker/README.md) · [Detailed guide](../../worker/docs/README.md).

## 1. Configuration

On Windows, run **00-Konfiguration.bat** and then **01-Installieren.bat** from the `worker/` directory. **02-Starten.bat** starts the default services; **03-Neustarten.bat** restarts running containers; **04-Verbindungsdaten.bat** creates a local text report with the LAN IP and ports. `scripts/windows/Setup.ps1` remains supported for compatibility.

Linux from worker:

```bash
bash scripts/linux/setup-linux.sh
```

These setup methods create a local .env **without a token** and preserve any existing .env. Restrict port 10300 to HA, port 10502 to HA and the CPU speech server, and port 11434 (if using Ollama) to HA.

## 2. Start services

```bash
docker compose config --quiet
docker compose up -d --build whisper
docker compose --profile stream up -d --build qwen-stream
```

Streaming supports /health, /stream (24 kHz PCM s16le mono), and /synthesize. The former non-streaming profile tts uses port 10501; do not run both TTS models at once. Prepare voice variants locally; see [worker reference](../../worker/docs/README.md).

Optional local LLM:

```bash
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
```

Ollama shares the GPU. Test services one at a time with limited VRAM. Use the private-LAN Ollama gateway through HA; no additional TAFA API key is required. Models may compete for GPU memory. The CPU setup does not require an extra GPU computer.

## Optional: vision

The vision profile shares Ollama, port 10503 restricted to HA. [Setup and API](../../worker/docs/README.md#optional-vision-180). HA camera selection is separate.

## 3. Connect GPU Whisper, CPU fallback and Ollama to Home Assistant

**Windows:** `04-Verbindungsdaten.bat` generates the TAFA JSON and an address TXT using the actual GPU `LAN_IP` from `.env`. The Proxmox CPU server is separate; its IP cannot be inferred.

1. **Install GPU Whisper via Wyoming Protocol:** HA → **Settings → Devices & services → Add integration → Wyoming Protocol**; host = `GPU-IP`, port = `10300`. Find the new real `stt.*` entity ID. In **Apps → TAFA → Configuration**, set `gpu_stt` to it and `gpu_stt_host` to the bare GPU IP (no URL scheme or port).
2. **Install CPU Whisper via Wyoming Protocol:** Add a **second** Wyoming integration for the Proxmox speech server at its own IP and port `10300`. Set `cpu_stt` to this separate `stt.*` entity. The CPU and GPU STT IDs must differ. One Wyoming STT provider may be auto-selected; with two providers, select both IDs explicitly.
3. **Configure Qwen TTS:** Set `gpu_base=http://GPU-IP:10502` and `hardware_profile=automatic` in **Apps → TAFA → Configuration**. This TTS URL does **not** automatically enable GPU Whisper.
4. **Install Ollama for open questions:** Optionally run `docker compose --profile llm up -d ollama ollama-gateway` on the GPU computer. Then HA → **Devices & services → Add integration → Ollama** using `http://GPU-IP:11434`. Add a conversation agent with an **installed** text model such as `qwen3:4b-instruct` and set TAFA `llm_agent` to the agent's **actual** `conversation.*` entity ID (not device name). Ollama text inference is separate from Qwen speech output.
5. **Check TAFA Lokal Assist pipeline:** STT = **Tablet Assist Sprachrouter** (GPU to CPU fallback), conversation = **Tablet Assist Gespraechsrouter** (Ollama agent), TTS = **Tablet Assist Stream** (Qwen to Piper fallback). Restart TAFA App after changing settings, and HA Core once after HA integration updates.
6. **Verify the actual recognition host:** After a spoken question, inspect the `stt.*` entity **Tablet Assist Sprachrouter**: `letztes_backend=zusatzrechner` = GPU; `homeserver` = CPU/fallback. `letzte_dauer_ms` includes audio reception; Android's end-of-speech pause and Ollama inference add separate delay.

For external CPU voice set `speech_mode=external` and `external_piper_base=http://PROXMOX-IP:5000`. The older optional Proxmox MP3 announcements setup still accepts its own local `/etc/jarvis-local.env`:

```ini
JARVIS_GPU_BASE=http://gpu.example.invalid:10502
```

Keep it root-only and restart `jarvis-mp3` where appropriate. Do not install the old `worker/proxmox/tts_router.py` alongside the main installer. Keep every port on the trusted LAN, without token-bearing public proxy routes.

## 4. Test

On Windows run Test-Stream.ps1 and Test-Voice.ps1 from the worker folder. On Linux test /health, /synthesize and /stream with local LAN addresses; no extra TAFA API credentials are needed. Do not expose keys in screenshots, logs or source control. Test native Assist playback and MP3 with the GPU host turned off.

## Jarvis model settings (1.8.0)

With the TAFA HA integration 0.4.3, the dashboard's **AI models and performance** panel selects installed text and vision models and a matching context (2048/4096/8192 tokens) and residency (0/60/120/300/600 seconds). Selecting `qwen3-vl:4b-instruct` for both avoids alternating model weights; verify real VRAM peaks alongside Whisper and TTS. Ollama still permits one loaded model and one parallel request. No automatic downloads, new service, public Ollama endpoint or volume changes are added. Legacy vision callers retain immediate unload by default.

The LAN-only `GET /runtime` reports only allowlisted installed/loaded models. `POST /describe` additionally accepts bounded `keep_alive` and `num_ctx` and reports inference timing metrics. The HA integration supplies saved parameters; its existing Ollama conversation agent receives matching settings through native config-subentry persistence, preserving prompts, tools and history. Worker endpoints are unprotected by a token: restrict host firewall access to HA. Camera-display commands still bypass both inference models. Settings changes apply on the next request; the first request after idle/restart may load the model.
