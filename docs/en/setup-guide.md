# TAFA – simplified first-time setup

[Deutsch](../setup-guide.md) · [Install the App](app.md)

> **Since App 0.3.12:** Manage TAFA settings exclusively at **Settings → Apps → TAFA → Configuration**; restart the App after saving. On upgrade, restart HA Core once for the updated integration, then restart the App to sync existing settings. Add the native Wyoming integration once in Devices & services, but choose its TAFA entity and configure all other TAFA options in the App. Existing Assist pipelines are preserved. Marketplace-only installations retain their HA options flow.


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

On the GPU computer, run `00-Konfiguration.bat` and `01-Installieren.bat` on Windows, or `bash scripts/linux/setup-linux.sh` on Linux. These create a local token-free `.env` if needed. Then run `docker compose --profile stream up -d --build qwen-stream`.

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

### Set up tablet and Multiroom without YAML

1. In the Android **TAFA Device Bridge → Connect**, use an active **non-admin HA account** and its own access token. Start wake recognition under **Wake word** so the tablet appears in **TAFA → Devices**.
2. As an **HA administrator**, open **TAFA → Devices** and choose the detected tablet. Under **Multiroom audio**, select the HA user, accept/edit the suggested room ID and click **Connect audio room**. Unchanged existing rooms and active players are preserved.
3. If this device belongs to another HA user, an administrator must explicitly confirm the ownership transfer; then use the selected account token on the tablet.
4. On Android enable **Multiroom audio** and **Start player**. **TAFA → Devices** now reports audio connected, player offline or playback not ready. For playback not ready, check the Bluetooth media output.
4. **Camera access (optional):** In **TAFA → Devices → Multiroom audio**, explicitly enable **“Allow camera access for this room”**. Camera sharing is disabled by default. Keep **Multiroom audio** enabled on the tablet and *explicitly* start camera streaming from Android. The room user's token is sufficient; no administrator token is needed. Enabling permission never starts capture by itself; disabling clears stored frames.

**Important:** Wake device registration and audio room pairing are separate systems. A registered wake device alone does not prove audio playback is connected. Each audio room requires its own active non-admin HA account; its assignment is managed in the TAFA Devices page rather than Developer tools. The dashboard does not store or display access tokens. The legacy `input_text.jarvis_native_audio_command` helper is not required in Multiroom mode.



### Test speech playback from a private HTTP address

Once the Android audio player shows connected under **TAFA → Devices**, open **Voice test** and click **“Test speech output”**. You can edit the sample phrase, then the selected **TAFA Lokal** Assist pipeline generates speech with Qwen/Piper and sends the result to the paired Android/Bluetooth player. Status shows synthesis, transfer, buffering, playback and final success/error, based on the actual tablet player report. **No browser microphone** is used, so this works on a private HTTP Home Assistant address.

**“Speak once”** remains the full microphone/Assist test, which browsers restrict to trustworthy HTTPS (or localhost). On insecure HTTP the microphone control is replaced by a helpful explanation rather than a broken button. No new Android APK, HA helpers or tokens are required.

### Test a spoken question after pairing a tablet

Open **TAFA → Devices → [tablet] → Voice test · Speak once** and expand the section. TAFA automatically selects an existing **TAFA Lokal** Assist pipeline with speech recognition and **Tablet Assist Stream**; another complete pipeline can be selected. Tap **Speak once**, grant browser microphone permission, ask a short question and hear the reply on the paired tablet/Bluetooth player. This reuses the tested Assist and room-audio transport; no additional HA helpers or scripts are required.

The browser requires **trusted HTTPS** (or localhost) for microphone access. A logged-in HA administrator may also run the test against an explicitly paired tablet shown in the Devices list; normal tablet accounts test only their own room. TTS uses Qwen with Piper fallback as usual. Closing the test or leaving the Devices view stops microphone capture. If no complete STT+TTS pipeline exists, TAFA links to Voice assistants setup.

This microphone flow runs in the **Home Assistant browser/dashboard**. Android **Device Bridge 1.0.0** still sends wake-word events only and does not record the subsequent question in the background.

### New native Android voice capture (Device Bridge 1.0.1)

For **Hey Jarvis → spoken question → Whisper → Qwen/Piper → Bluetooth**, Android needs a complete Home Assistant Assist pipeline, **TAFA Lokal**, with the TAFA speech router (Whisper/STT), conversation router and TAFA stream (TTS). The TAFA App creates it automatically as soon as all three HA entities exist, **including with an external Proxmox speech server**. Until then, the App displays **waiting_for_entities** rather than incorrectly reporting **external_ready**. In external mode, register the speech server's Wyoming STT integration in Home Assistant. TAFA automatically selects the only available Wyoming STT provider; with multiple providers, choose one under **Settings → Apps → TAFA → Configuration → cpu_stt**.

Under **TAFA → Devices → Voice test** the UI reports whether a complete Assist pipeline is configured. This confirms configuration, **not** live Whisper availability. On Android 1.0.1, explicitly enable the optional mode under **Wakeword → Native voice conversation**. The existing paired room and non-admin HA account token remain in use. Native capture needs no browser microphone or browser HTTPS. Local HTTP transport remains unencrypted. The Android 1.0.1 APK still requires the original signing key.

## Where to configure

**First:** Open **Settings → Apps → TAFA → Configuration** and configure Proxmox/Piper, GPU/Qwen, Alexa MP3, automatic Piper fallback, voice and sound profile. Restart the App. Live **Connection diagnostics** and safe TAFA-only CPU model cleanup are in **Apps → TAFA → Web UI**. Existing App-managed integration settings are synchronized from App Configuration on restart.


1. Open **Apps → TAFA → Web UI** for status and guidance.
2. Manage Piper, Wyoming entity ID (`cpu_stt`), Qwen, Alexa and optional data sources in **Settings → Apps → TAFA → Configuration**. There is no second TAFA options screen for App-managed installations.
3. Save to reload TAFA. No extra TAFA API key is needed for GPU/MP3 LAN services; clear GPU URL to disable GPU TTS.
4. Inspect **Settings → Voice assistants → TAFA Lokal**. Select **Tablet Assist Stream** for automatic Qwen/Piper routing.

Test local Assist, external Piper health at `http://SERVER:5000/health`, optional GPU-on/GPU-off fallback, and finally an optional harmless Alexa announcement over HTTPS.

The unchanged Device Bridge 1.0.0 emits wake events only; another active Assist client needs to record the following question. The private dashboard is excluded. GPU hosts, DNS, proxy and routers are deliberately not auto-discovered or changed.

### Ollama rejects the first question (TAFA App 0.3.17 / integration 0.4.9)

A newly created Ollama conversation entity has Home Assistant state `unknown` until it handles its first message. That is **normal**; TAFA integration 0.4.8 incorrectly treated it as offline. Since 0.4.9, TAFA forwards the first request. Confirm the actual Ollama `conversation.*` entity ID under **Settings → Devices & services → Ollama → Conversation agent → Entity** and set it in **Apps → TAFA → Configuration → llm_agent**. After updating TAFA App, **restart Home Assistant Core once**, then **restart TAFA App** to synchronize settings. An actual `unavailable` state remains an error. The CPU hardware profile only governs Qwen/Piper TTS and no longer disables Ollama conversation. No Android update required.

### Choose CPU/GPU Wyoming entities from dropdowns (TAFA App 0.3.18)

Under **Settings → Apps → TAFA → Control Center**, the **“Automatically discover Wyoming STT”** section lists current enabled Home Assistant Wyoming `stt.*` entities in two dropdowns. Explicitly assign **CPU Whisper / Proxmox** and **GPU Whisper / Windows** to *different* entities, save and **restart the TAFA App**. Unrelated options and existing audio/camera mappings are preserved.

If only CPU STT appears, GPU Whisper has not yet been registered in Home Assistant. Add **Wyoming Protocol** under **Devices & services**, with the GPU worker host and TCP **10300**, then reopen the Control Center. The Qwen TTS URL on port 10502 does **not** activate GPU transcription. After a spoken question check the **Tablet Assist Sprachrouter** entity attribute `letztes_backend`: `zusatzrechner` = GPU, `homeserver` = CPU. An old Fast Whisper log entry alone does not verify which backend handled the last question.
