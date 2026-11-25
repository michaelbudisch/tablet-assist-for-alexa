# TAFA App 0.3.17 documentation

[Deutsch](../docs/app.md) · [Project overview](../README.md)

> **Since App 0.3.12:** Manage TAFA settings exclusively at **Settings → Apps → TAFA → Configuration**; restart the App after saving. On upgrade, restart HA Core once for integration 0.4.4, then restart the App to sync existing settings. Add the native Wyoming integration once in Devices & services, but choose its TAFA entity and configure all other TAFA options in the App. Existing Assist pipelines are preserved. Marketplace-only installations retain their HA options flow.


**TAFA App 0.3.13 — release candidate, not yet certified on a clean HA OS device.** Requirements: Home Assistant OS 2026.11+ and a supported amd64/aarch64 machine; enough memory and disk space for German CPU speech models. Android Device Bridge 1.0.0 is unchanged.

## One-App setup

1. Create a Home Assistant backup. Prefer a clean test instance for the first deployment.
2. Open **Settings → Apps → Install app → Repositories**, add `https://github.com/michaelbudisch/tablet-assist-for-alexa`, select **TAFA**, install and start.
3. Open the **TAFA Control Center**. CPU models download on first launch (network access needed). The status tiles distinguish real Piper/Whisper readiness from pending or failed initialization.
4. TAFA stages **one** component: `custom_components/tablet_assist_for_alexa`. Restart Home Assistant **once** using the normal Home Assistant settings. No YAML edits or second HA integration are needed on a fresh installation.
5. The App attempts the HA integration config flow through the Supervisor Core API and then creates a **TAFA Lokal** Assist pipeline when STT, TTS and the conversation router are registered. Existing HA pipelines remain untouched. If automatic setup is unavailable, open **Settings → Devices & services → Add integration → TAFA**, then select the built-in Piper service and HA Assist pipeline from Control Center. Do not manually edit `.storage`.
6. Install/connect the existing [TAFA Device Bridge 1.0.0](../android/README.md); select the TAFA Lokal pipeline in Home Assistant Assist (or the HA Companion app), not in Device Bridge. Optionally pair an Echo as the Android Bluetooth output. The app's audio, camera and wake-word permissions remain under Android user control.

## Native wake-word limitation

Device Bridge 1.0.0 sends the recognized wake word and releases its microphone but does not transmit the following question. An active Assist client must capture the question after that event; no backend-only change can recover missing audio. Direct manual Assist works. Do not advertise fully hands-free operation with only the unchanged Bridge until the handoff is independently tested and supported.

## What is bundled

- One HA integration provides STT, TTS, conversation, native wake-device registry, authenticated compatibility API, multiroom audio, optional cameras/motion and vision services.
- The App contains **local German Piper and Faster-Whisper CPU engines**. Their downloaded models persist in the HA App's `/data` volume. They listen on the internal app network; no public port is mapped.
- The GPU worker, Ollama and Alexa MP3/HTTPS notifications remain optional and must be configured separately.
- **Alexa Devices MP3 tip (confirmed in a real TAFA test):** For Qwen MP3 audio, map `Alexa rooms (JSON)` to the **Speak** Notify entity (`notify.…_sprechen`), not **Announce** (`notify.…_durchsagen`). The latter can play only the Alexa chime even when ordinary text works. Example: `{"Büro":{"notify":"notify.buro_dot_sprechen"}}`. Verify your Echo's actual entity ID in Home Assistant. See [Alexa MP3 setup and troubleshooting](../docs/en/setup-guide.md#3-optional-alexa-mp3-announcements-over-https).
- This App does not install the private TAFA dashboard or modify Android/APK source.

## Updates, safety and limitations

- The App automatically stages the integration and updates it **only if TAFA originally installed it and its files are unchanged**. Before a managed update it saves the prior version under `<HA config>/.tafa/rollback`. HACS/manual installations and edited files are never overwritten. Restart HA after backend updates.
- An older configured `jarvis_tablet_audio` can conflict with duplicate native endpoints. TAFA detects it and skips duplicate registration; it does not delete, overwrite or automatically migrate the old integration. Backup and migrate separately.
- Microphones/cameras are opt-in. Audio/STT requests are processed in memory; the built-in speech API limits request sizes. Initial model downloads need internet; there is no guaranteed offline first install.
- Known release gate: clean HA OS install, model download, end-to-end Assist/Device Bridge/Bluetooth and simultaneous physical Multiroom tests still need confirmation. See [release checklist](../docs/en/release.md).

[Marketplace-only instructions](marketplace.md) · [Multiroom](../homeassistant/examples/MULTIROOM.md) · [Optional GPU worker](worker.md)

### Set up tablet and Multiroom without YAML

1. In the Android **TAFA Device Bridge → Connect**, use an active **non-admin HA account** and its own access token. Start wake recognition under **Wake word** so the tablet appears in **TAFA → Devices**.
2. As an **HA administrator**, open **TAFA → Devices** and choose the detected tablet. Under **Multiroom audio**, select the HA user, accept/edit the suggested room ID and click **Connect audio room**. Unchanged existing rooms and active players are preserved.
3. If this device belongs to another HA user, an administrator must explicitly confirm the ownership transfer; then use the selected account token on the tablet.
4. On Android enable **Multiroom audio** and **Start player**. **TAFA → Devices** now reports audio connected, player offline or playback not ready. For playback not ready, check the Bluetooth media output.

**Important:** Wake device registration and audio room pairing are separate systems. A registered wake device alone does not prove audio playback is connected. Each audio room requires its own active non-admin HA account; its assignment is managed in the TAFA Devices page rather than Developer tools. The dashboard does not store or display access tokens. The legacy `input_text.jarvis_native_audio_command` helper is not required in Multiroom mode.



### Test a spoken question after pairing a tablet

Open **TAFA → Devices → [tablet] → Voice test · Speak once** and expand the section. TAFA automatically selects an existing **TAFA Lokal** Assist pipeline with speech recognition and **Tablet Assist Stream**; another complete pipeline can be selected. Tap **Speak once**, grant browser microphone permission, ask a short question and hear the reply on the paired tablet/Bluetooth player. This reuses the tested Assist and room-audio transport; no additional HA helpers or scripts are required.

The browser requires **trusted HTTPS** (or localhost) for microphone access. A logged-in HA administrator may also run the test against an explicitly paired tablet shown in the Devices list; normal tablet accounts test only their own room. TTS uses Qwen with Piper fallback as usual. Closing the test or leaving the Devices view stops microphone capture. If no complete STT+TTS pipeline exists, TAFA links to Voice assistants setup.

This microphone flow runs in the **Home Assistant browser/dashboard**. Android **Device Bridge 1.0.0** still sends wake-word events only and does not record the subsequent question in the background.


### Test speech playback from a private HTTP address

Once the Android audio player shows connected under **TAFA → Devices**, open **Voice test** and click **“Test speech output”**. You can edit the sample phrase, then the selected **TAFA Lokal** Assist pipeline generates speech with Qwen/Piper and sends the result to the paired Android/Bluetooth player. Status shows synthesis, transfer, buffering, playback and final success/error, based on the actual tablet player report. **No browser microphone** is used, so this works on a private HTTP Home Assistant address.

**“Speak once”** remains the full microphone/Assist test, which browsers restrict to trustworthy HTTPS (or localhost). On insecure HTTP the microphone control is replaced by a helpful explanation rather than a broken button. No new Android APK, HA helpers or tokens are required.


### New native Android voice capture (Device Bridge 1.0.1)

For **Hey Jarvis → spoken question → Whisper → Qwen/Piper → Bluetooth**, Android needs a complete Home Assistant Assist pipeline, **TAFA Lokal**, with the TAFA speech router (Whisper/STT), conversation router and TAFA stream (TTS). The TAFA App creates it automatically as soon as all three HA entities exist, **including with an external Proxmox speech server**. Until then, the App displays **waiting_for_entities** rather than incorrectly reporting **external_ready**. In external mode, register the speech server's Wyoming STT integration in Home Assistant. TAFA auto-selects one Wyoming STT provider; if multiple are installed, set **cpu_stt** under **Settings → Apps → TAFA → Configuration**.

Under **TAFA → Devices → Voice test** the UI reports whether a complete Assist pipeline is configured. This confirms configuration, **not** live Whisper availability. On Android 1.0.1, explicitly enable the optional mode under **Wakeword → Native voice conversation**. The existing paired room and non-admin HA account token remain in use. Native capture needs no browser microphone or browser HTTPS. Local HTTP transport remains unencrypted. The Android 1.0.1 APK still requires the original signing key.


**Ollama first-question fix:** The normal initial `unknown` state of a new HA conversation entity is now accepted. In App Configuration select the exact Ollama `conversation.*` entity, restart HA Core after the component upgrade, then restart TAFA App to synchronize. App 0.3.17 / HA integration 0.4.9. No Android rebuild.
