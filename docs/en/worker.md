# Optional TAFA GPU Worker

[Deutsch](../worker.md) · [TAFA installation](setup-guide.md)

**GPU Worker 2.2.7** adds GPU Wyoming Whisper (TCP **10300**), Qwen streaming TTS (**10502**), a single always-resident `qwen3-vl:4b-instruct` Ollama model shared by text and Vision (**11434**/**10503**). **CPU speech services** remain separate: run them **locally in the TAFA App** or on an **external speech server**. Keep these APIs on a firewall-restricted trusted LAN.

**Windows:** From `worker/` run **01-Installieren.bat**, then **04-Verbindungsdaten.bat** to generate `tafa-worker.json` and `GPU-Worker-Verbindungsdaten.txt`. Import under **TAFA → Connections → Quick setup via JSON**, **check and confirm**. The separate CPU backend is not included in this GPU export.

**Home Assistant:** Add **Wyoming Protocol** under **Devices & services** for the GPU IP on TCP **10300**, then select the new **GPU `stt.*` entity in TAFA → Connections**. Fast GPU check uses a bare IP with no port. For Ollama, additionally install the HA **Ollama** integration and select its `conversation.*` agent. **Qwen TTS alone does not enable GPU Wyoming STT.**

**Assist pipeline:** STT **Tablet Assist Sprachrouter**, conversation **Tablet Assist Gespraechsrouter**, TTS **Tablet Assist Stream**. GPU Whisper can fall back to CPU STT and GPU Qwen to Piper; **a CPU text-LLM fallback does not exist automatically**.

For full prerequisites, Windows/Linux commands, testing and optional Vision, see the [current worker installation guide](../../worker/docs/README.md) and [Windows quick start](../../worker/README.md).
