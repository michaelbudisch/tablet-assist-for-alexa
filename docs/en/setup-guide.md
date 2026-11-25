# TAFA – simplified first-time setup

[Deutsch](../setup-guide.md) · [Install the App](app.md)

> **New in App 0.3.12:** Manage TAFA settings exclusively at **Settings → Apps → TAFA → Configuration**; restart the App after saving. On upgrade, restart HA Core once for integration 0.4.4, then restart the App to sync existing settings. Add the native Wyoming integration once in Devices & services, but choose its TAFA entity and configure all other TAFA options in the App. Existing Assist pipelines are preserved. Marketplace-only installations retain their HA options flow.


TAFA App **0.3.12** can use bundled CPU Piper/Whisper or a trusted **Proxmox-only speech server**. Choose under **Settings → Apps → TAFA → Configuration** before starting. There are three independent choices.

**Existing speech server:** To update only the MP3 generator from an older token-based version, use the source checkout inside the dedicated Debian guest and run `sudo bash proxmox/update-mp3-generator.sh`. It backs up the existing `api.py` and restarts only `jarvis-mp3.service`, rolling back if health checks fail. This does not replace Piper, Whisper, data or your proxy. Update the matching TAFA integration to 0.4.3. Never run this script on the Proxmox host. No public forwarding for port 5001.

## 1. Where should Piper and Whisper run?

| Mode | Result | Setup |
|---|---|---|
| **TAFA local (default)** | Piper and Whisper inside the TAFA App | Start the App, restart HA once, check the TAFA Lokal pipeline |
| **External Proxmox speech server** | No bundled CPU model download/startup | Set `speech_mode=external`, `external_piper_base=http://SERVER:5000` and restart the App; add Wyoming STT `SERVER:10300` in HA |

Follow the [CPU speech server guide](proxmox.md). Run `install-speechserver.sh` only inside a **new Debian guest**, never on the Proxmox host or over an existing Jarvis installation. `create-ct.sh` creates a dedicated guest after confirmation (4 vCPU, 4 GiB RAM, 20 GiB disk, DHCP). It also supplies the optional MP3 generation services.

External mode checks private Proxmox Piper `/health` and can prepare the TAFA integration without downloading built-in models. In **Settings → Apps → TAFA → Configuration**, verify Piper and select the separately configured Wyoming STT entity for `SERVER:10300` as CPU STT. Then create/select an Assist pipeline using the TAFA STT router and **Tablet Assist Stream**. Proxmox Piper has no `/stt` endpoint, so the Wyoming integration is required.

## 2. Optional Qwen GPU voice

On the GPU computer, run `00-Konfiguration.bat` and `01-Installieren.bat` on Windows, or `bash setup-linux.sh` on Linux. These create a local token-free `.env` if needed. Then run `docker compose --profile stream up -d --build qwen-stream`.

Under **Apps → TAFA → Configuration**, set **Automatic**, streaming URL `http://GPU-PC:10502`, (no API token needed). GPU Wyoming STT on port `10300` is optional. Select **Tablet Assist Stream** as the Assist pipeline's TTS engine. Qwen takes over when healthy; Piper falls back when the GPU fails **before audio playback starts**. Existing Assist pipelines are not silently changed. [GPU worker guide](worker.md).

## 3. Optional Alexa MP3 announcements over HTTPS

Not needed for tablet-to-Echo Bluetooth output. The Proxmox speech server has a LAN-only MP3 generator on `5001` and temporary audio files on `8080`. Follow the [Nginx HTTPS proxy guide](nginx-proxy.md) for a valid public HTTPS hostname. In **Apps → TAFA → Configuration**, set MP3 generator address, public HTTPS origin and room/notify mapping. Never open internal speech/GPU ports publicly; never expose internal generator ports.

### Alexa Devices: use **Speak**, not **Announce**, for Qwen MP3 playback

**Observed with the Home Assistant Alexa Devices integration:** Selecting **Announce** (`notify.…_durchsagen`) produced the Alexa chime without playing the generated MP3. Selecting **Speak** (`notify.…_sprechen`) played the Qwen MP3 successfully. TAFA delivers an `<audio src="https://…/file.mp3"/>` tag through the configured Notify entity. Plain text may still work with Announce, so a successful text announcement does not prove MP3 support.

1. In **Settings → Devices & services → Entities**, confirm the exact entity ID for **“[Echo name] – Speak”**.
2. In **Settings → Apps → TAFA → Configuration → Alexa rooms (JSON)** enter the Speak entity, for example:

   ```json
   {"Büro":{"notify":"notify.buro_dot_sprechen"}}
   ```

3. Save the App options, restart TAFA, then retry the announcement in **TAFA → Alexa announcements**. Reload the HA integration if necessary.

If you **hear a chime but no voice**, check the Notify entity first; next verify that the temporary MP3 is available through the configured public HTTPS URL. The Speak entity may omit the Alexa announcement chime; you can optionally enable TAFA's own MP3 chime. Other Alexa integrations may behave differently.

## Where to configure

**First:** Open **Settings → Apps → TAFA → Configuration** and configure Proxmox/Piper, GPU/Qwen, Alexa MP3, automatic Piper fallback, voice and sound profile. Restart the App. Live **Connection diagnostics** and safe TAFA-only CPU model cleanup are in **Apps → TAFA → Web UI**. Existing App-managed integration settings are synchronized from App Configuration on restart.


1. Open **Apps → TAFA → Web UI** for status and guidance.
2. Manage Piper, Wyoming entity ID (`cpu_stt`), Qwen, Alexa and optional data sources in **Settings → Apps → TAFA → Configuration**. There is no second TAFA options screen for App-managed installations.
3. Save to reload TAFA. No extra TAFA API key is needed for GPU/MP3 LAN services; clear GPU URL to disable GPU TTS.
4. Inspect **Settings → Voice assistants → TAFA Lokal**. Select **Tablet Assist Stream** for automatic Qwen/Piper routing.

Test local Assist, external Piper health at `http://SERVER:5000/health`, optional GPU-on/GPU-off fallback, and finally an optional harmless Alexa announcement over HTTPS.

The unchanged Device Bridge 1.0.0 emits wake events only; another active Assist client needs to record the following question. The private dashboard is excluded. GPU hosts, DNS, proxy and routers are deliberately not auto-discovered or changed.
