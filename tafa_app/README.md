# TAFA Home Assistant App 0.3.15 — release candidate

The Ingress Control Center installs and safely upgrades one unified HA integration. Choose local Piper/Faster-Whisper (default), or external Proxmox Piper/Whisper with `speech_mode=external` and `external_piper_base=http://PROXMOX-IP:5000` in the App Configuration before starting. External mode skips local model processes and downloads. the Android Device Bridge stays unchanged. [English guide](../docs/en/app.md) · [Deutsche Anleitung](../docs/app.md).

No private dashboard is shipped. A Home Assistant Core restart is required after first install or backend update. Clean HA OS and hardware tests are still pending.

All App-managed HA integration settings are now maintained in **Apps → TAFA → Configuration** (App restart required). Built-in HA configuration flows remain available for Marketplace-only installations. On upgrade, restart HA Core once to load integration 0.4.4, then restart TAFA to synchronize existing settings. Advanced source and room mappings are optional JSON fields.

**New in 0.3.13:** Administrators pair registered tablets directly in **TAFA → Devices → Multiroom audio**. Select an existing non-admin HA user and room; status shows audio offline/online/ready without YAML. Use the same HA user token on the Android Device Bridge; enable Multiroom audio and start its player. Existing room settings remain in place. [Full steps](../docs/en/setup-guide.md).

**New in 0.3.14:** Open **TAFA → Devices → Voice test** on a trusted HTTPS Home Assistant page, and use **Speak once** to test the full STT/Assist/TTS path to the paired tablet. See [setup instructions](../docs/en/setup-guide.md).

**App 0.3.15:** **TAFA → Devices → Voice test → Test speech output** now works from private HTTP with the selected Qwen/Piper TTS engine and confirmed Android room playback. Browser microphone questions still need HTTPS.
