# TAFA Home Assistant App 0.3.20 — release candidate

The Ingress Control Center installs and safely upgrades one unified HA integration. Choose local Piper/Faster-Whisper (default), or external Proxmox Piper/Whisper with `speech_mode=external` and `external_piper_base=http://PROXMOX-IP:5000` in the App Configuration before starting. External mode skips local model processes and downloads. the Android Device Bridge stays unchanged. [English guide](../docs/en/app.md) · [Deutsche Anleitung](../docs/app.md).

No private dashboard is shipped. A Home Assistant Core restart is required after first install or backend update. Clean HA OS and hardware tests are still pending.

Use **TAFA Control Center → Settings** for day-to-day configuration. All controls write the existing Supervisor App options, just like the technical **Apps → TAFA → Configuration** editor (advanced fallback; App restart required). Built-in HA configuration flows remain available for Marketplace-only installations. On upgrade, restart HA Core once to load integration 0.4.4, then restart TAFA to synchronize existing settings. Advanced source and room mappings are optional JSON fields.

**New in 0.3.13:** Administrators pair registered tablets directly in **TAFA → Devices → Multiroom audio**. Select an existing non-admin HA user and room; status shows audio offline/online/ready without YAML. Use the same HA user token on the Android Device Bridge; enable Multiroom audio and start its player. Existing room settings remain in place. [Full steps](../docs/en/setup-guide.md).

**New in 0.3.14:** Open **TAFA → Devices → Voice test** on a trusted HTTPS Home Assistant page, and use **Speak once** to test the full STT/Assist/TTS path to the paired tablet. See [setup instructions](../docs/en/setup-guide.md).

**App 0.3.15:** **TAFA → Devices → Voice test → Test speech output** now works from private HTTP with the selected Qwen/Piper TTS engine and confirmed Android room playback. Browser microphone questions still need HTTPS.

**New in 0.3.16:** External Proxmox mode now checks the complete Home Assistant Assist pipeline before reporting ready. When Wyoming STT is missing, configure it in HA. A single Wyoming STT provider is chosen automatically; with multiple providers, set `cpu_stt` in TAFA App options. The App retries automatically. See [native Android setup](../docs/en/setup-guide.md).

**Fix in 0.3.17 / integration 0.4.9:** A freshly configured Ollama conversation entity initially has HA state `unknown`, which previously caused TAFA to refuse its first question. Update the App, restart Home Assistant Core once for the integration update, and restart the App to sync your selected `llm_agent`. No new Android APK is needed.

**New in 0.3.18:** Under **TAFA Control Center → Automatically discover Wyoming STT**, select detected Home Assistant Wyoming speech entities from two dropdowns (**CPU** for Proxmox and **GPU** for Windows). The entries are saved to TAFA App Configuration without overwriting unrelated settings; **restart the TAFA App** to apply. If GPU Whisper is missing, install **Wyoming Protocol** in HA with GPU host and port 10300 first. The regular **Apps → TAFA → Configuration** static form still allows manually editing these fields.

**Hotfix 0.3.19:** Rebuild/update TAFA to fix the missing Wyoming picker module in the 0.3.18 Docker image. Saved settings are retained and no Android update is needed.

**App 0.3.20:** The Control Center now has one grouped settings editor (Piper, Wyoming CPU/GPU, Qwen, Ollama, Alexa, voice and advanced sources). The technical HA Configuration editor remains available for recovery and to choose `speech_mode=external` *before the first launch* if local CPU models should never download. Save and restart TAFA; there is no second settings store.

### Voice test in TAFA Control Center (0.3.45)

Open **Speak now** at the far right of the Control Center navigation. Use **Muted** (manual push-to-talk remains available), **Wake word** (browser audio is transcribed through Whisper; not the Android native wakeword engine), or **Always on** (the visible browser page automatically listens for the next utterance). Microphone access requires HTTPS and explicit browser permission. Recording stops when the page is hidden or you switch away.

The **TAFA Lokal** Assist pipeline is used without changing your other assistants, devices, automations or configuration. The page displays the current pipeline, recognized question, answer, measured STT/conversation/TTS stages, and available HA router attributes. Audio can be replayed through the browser only; this is not an Alexa/Echo output test. Conversation history is retained only in the current browser page and clears on reload. No microphone recordings or transcripts are written to disk.

**Security:** Only administrator Ingress sessions may use the test; every request has CSRF validation, audio is capped at 30 seconds, and TTS playback is restricted to Home Assistant's local TTS proxy. Spoken commands run real HA Assist intents and may control your configured devices, just as in the normal Assist pipeline.
