# TAFA – simplified first-time setup

[Deutsch](../setup-guide.md) · [Install the App](app.md)

The TAFA Home Assistant App includes **local CPU Piper and Faster-Whisper**. For basic setup you need **no** Proxmox speech server, GPU computer or HTTPS proxy. There are three independent choices.

**Existing speech server:** To update only the MP3 generator from an older token-based version, use the source checkout inside the dedicated Debian guest and run `sudo bash proxmox/update-mp3-generator.sh`. It backs up the existing `api.py` and restarts only `jarvis-mp3.service`, rolling back if health checks fail. This does not replace Piper, Whisper, data or your proxy. Update the matching TAFA integration to 0.4.3. Never run this script on the Proxmox host. No public forwarding for port 5001.

## 1. Where should Piper and Whisper run?

| Mode | Result | Setup |
|---|---|---|
| **TAFA local (default)** | Piper and Whisper inside the TAFA App | Start the App, restart HA once, check the TAFA Lokal pipeline |
| **External Proxmox speech server** | Piper and Whisper in a dedicated Debian VM/container | Piper `http://SERVER:5000`, Wyoming STT `SERVER:10300` |

Follow the [CPU speech server guide](proxmox.md). Run `install-speechserver.sh` only inside a **new Debian guest**, never on the Proxmox host or over an existing Jarvis installation. `create-ct.sh` creates a dedicated guest after confirmation (4 vCPU, 4 GiB RAM, 20 GiB disk, DHCP). It also supplies the optional MP3 generation services.

In **Settings → Devices & services → TAFA → Options → Speech servers & GPU**, enter the Piper URL. Add the Wyoming integration pointing to `SERVER:10300` and select that STT entity. **Note:** choosing external services does not currently stop the App's built-in CPU processes; it changes HA routing only.

## 2. Optional Qwen GPU voice

On the GPU computer, from `worker/` run `.\Setup.ps1` (Windows PowerShell) or `bash setup-linux.sh` (Linux). These create a local secret `.env` if none exists. Then run `docker compose --profile stream up -d --build qwen-stream`.

Under **TAFA Options → Speech servers & GPU**, set **Automatic**, streaming URL `http://GPU-PC:10502`, (no API token needed). GPU Wyoming STT on port `10300` is optional. Select **Tablet Assist Stream** as the Assist pipeline's TTS engine. Qwen takes over when healthy; Piper falls back when the GPU fails **before audio playback starts**. Existing Assist pipelines are not silently changed. [GPU worker guide](worker.md).

## 3. Optional Alexa MP3 announcements over HTTPS

Not needed for tablet-to-Echo Bluetooth output. The Proxmox speech server has a LAN-only MP3 generator on `5001` and temporary audio files on `8080`. Follow the [Nginx HTTPS proxy guide](nginx-proxy.md) for a valid public HTTPS hostname. In **TAFA Options → Alexa announcements & HTTPS**, set MP3 generator address, public HTTPS origin and room/notify mapping. Never open internal speech/GPU ports publicly; never expose internal generator ports.

## Where to configure

1. Open **Apps → TAFA → Web UI** for status and guidance.
2. Open **Settings → Devices & services → TAFA → Options** and select **Speech servers & GPU**, **Alexa announcements & HTTPS** or **Data sources & reminders**.
3. Save to reload TAFA. Leave password fields blank to retain saved keys; clear GPU URL to disable GPU TTS.
4. Inspect **Settings → Voice assistants → TAFA Lokal**. Select **Tablet Assist Stream** for automatic Qwen/Piper routing.

Test local Assist, external Piper health at `http://SERVER:5000/health`, optional GPU-on/GPU-off fallback, and finally an optional harmless Alexa announcement over HTTPS.

The unchanged Device Bridge 1.0.0 emits wake events only; another active Assist client needs to record the following question. The private dashboard is excluded. GPU hosts, DNS, proxy and routers are deliberately not auto-discovered or changed.
