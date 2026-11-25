# TAFA Home Assistant App 0.3.12 — release candidate

The Ingress Control Center installs and safely upgrades one unified HA integration. Choose local Piper/Faster-Whisper (default), or external Proxmox Piper/Whisper with `speech_mode=external` and `external_piper_base=http://PROXMOX-IP:5000` in the App Configuration before starting. External mode skips local model processes and downloads. the Android Device Bridge stays unchanged. [English guide](../docs/en/app.md) · [Deutsche Anleitung](../docs/app.md).

No private dashboard is shipped. A Home Assistant Core restart is required after first install or backend update. Clean HA OS and hardware tests are still pending.

All App-managed HA integration settings are now maintained in **Apps → TAFA → Configuration** (App restart required). Built-in HA configuration flows remain available for Marketplace-only installations. On upgrade, restart HA Core once to load integration 0.4.4, then restart TAFA to synchronize existing settings. Advanced source and room mappings are optional JSON fields.
