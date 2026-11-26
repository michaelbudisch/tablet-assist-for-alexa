# TAFA GPU Worker 2.2.6 – installation

[Deutsch](README.de.md) · [Quick start](../README.md) · [TAFA setup](../../docs/en/setup-guide.md)

The GPU worker is **optional**, adding GPU Wyoming Whisper (STT), Qwen streaming voice (TTS), optional Ollama text AI and Vision to an existing CPU-capable TAFA setup. A supported **NVIDIA GPU** is required. Windows needs NVIDIA drivers, Docker Desktop with **WSL2/Linux containers**; Linux needs Docker Engine/Compose and NVIDIA Container Toolkit. First model builds/downloads need Internet access and sufficient SSD space.

## Windows quick start

From the `worker/` directory:

1. Run `01-Installieren.bat` (or optionally `00-Konfiguration.bat` to create a missing `.env`). This sets up **Whisper and Qwen**, optionally offers **text Ollama**, then offers **Vision for tablet camera analysis (default Yes)**. Downloads of text and vision models each require separate consent.
2. `02-Starten.bat` starts configured services; `03-Neustarten.bat` restarts active containers.
3. `04-Verbindungsdaten.bat` generates **`tafa-worker.json`** and **`GPU-Worker-Verbindungsdaten.txt`**, opens the text report, and **does not start services**. It uses the `LAN_IP` in the local `.env` and current service state; stopped services appear as `enabled: false`.
4. In **TAFA Control Center → Connections → Quick setup via JSON**, select `tafa-worker.json`, **check configuration**, and confirm GPU endpoints. Finish selecting real HA entities as explained below.

To retrofit Vision into an existing Windows GPU worker, run **`05-Vision-Einrichten.bat`** in the root worker folder. Other optional Windows helpers live in `scripts/windows/` (`05-Ollama-Einrichten.bat`, `Worker-Windows.ps1` and `tests/`). Existing `.env` and Docker volumes are preserved.

## Linux and manual Docker setup

From `worker/`:

```bash
bash scripts/linux/setup-linux.sh
docker compose config --quiet
docker compose up -d --build whisper
docker compose --profile stream up -d --build qwen-stream
```

Optional **text AI**:

```bash
docker compose --profile llm up -d ollama ollama-gateway
docker compose exec ollama ollama pull qwen3:4b-instruct
```

The Windows JSON/TXT exporter is **not included** in the Linux bootstrap: enter endpoint URLs manually in TAFA **Connections**. Services share GPU memory; check VRAM and start optional models individually if needed.

## Where do the addresses belong?

| Service | GPU address | One-time HA step | TAFA Control Center |
| --- | --- | --- | --- |
| GPU Whisper/STT | `GPU-IP:10300` | Add **Wyoming Protocol**, find its `stt.*` entity | **Connections → GPU/AI:** GPU Wyoming STT and **fast GPU check** (bare IP) |
| Qwen/TTS | `http://GPU-IP:10502` | Select **Tablet Assist Stream** as Assist TTS | **Connections → GPU/AI:** Qwen URL |
| Ollama/text AI (optional) | `http://GPU-IP:11434` | Add **Ollama**, install a model and create a conversation agent | **Connections → GPU/AI:** actual `conversation.*` entity |
| CPU fallback | External: `CPU-IP:10300`, `http://CPU-IP:5000`; local: TAFA App | For external CPU, add a **separate Wyoming Protocol** with a distinct `stt.*` entity | **Connections → CPU fallback**; select speech mode under **Settings** |

**Important:** Qwen TTS does **not** automatically enable GPU Whisper. HA's Wyoming integration must create the GPU `stt.*` entity. The JSON report includes **GPU endpoints only**; it cannot guess a CPU host or create HA Wyoming/Ollama entities. Finish this configuration manually.

**Fallback:** **Tablet Assist Sprachrouter** can use configured CPU STT when GPU recognition is offline; **Tablet Assist Stream** can switch from Qwen to Piper if Qwen fails **before playback begins**. Neither automatically creates a **CPU LLM fallback** for offline GPU Ollama.

## Testing and operation

Verify endpoints in TAFA **Connections**, confirm the three routers in **TAFA Lokal**, then ask a spoken question with GPU online and stopped. STT router attributes indicate the actual recognition backend; TCP reachability alone is not a transcription test. Browser **Speak now** plays audio in the browser; test Android/Echo output separately.

Qwen serves `/health`, `/stream` and `/synthesize` on **10502**. Older non-streaming TTS uses **10501** and should not run at the same time. Windows now offers Vision during installation and allows retrofitting it using **`05-Vision-Einrichten.bat`**. On Linux/manually, run `docker compose --profile vision up -d --build ollama vision`, then (only after consenting to a multi-GB download) `docker compose --profile vision exec -T ollama ollama pull qwen3-vl:4b-instruct`. Verify `http://GPU-IP:10503/health` returns `ready: true`. A running Vision container without an installed model is **not ready**. The Windows TXT report includes the Vision endpoint and readiness; the v1 JSON stays compatible with older TAFA releases and contains only existing endpoints. HA infers the Vision host and port from the configured GPU-TTS address. Camera permission in HA is separate. More advanced and historical details are retained in [legacy worker reference](archive/legacy-worker-guide.en.md).

**Security:** These token-free APIs must be restricted to a **trusted LAN**. Restrict **10300**, **10502**, **10503**, **11434** and optional **10501** with your firewall; never port-forward the worker. Do not commit private `.env` or generated JSON/TXT containing LAN details.
