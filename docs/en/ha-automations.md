# Optional Home Assistant automations with TAFA

[Deutsch](../ha-automations.md) · [Project](../../README.md) · [Current setup](setup-guide.md)

**For fresh installations:** The TAFA App sets up its speech backend and dashboard. It does **not** import, rename, replace or enable existing private household automations. Washing machine, camera, greeting, quiet-hours and Alexa announcement automations require **user-specific HA entities and explicit configuration**.

## Recommended workflow

1. Complete [TAFA Lokal](setup-guide.md), the Android Device Bridge and room audio pairing first; verify a physical spoken request and playback.
2. Do **not** configure a public Alexa MP3 domain for regular Bluetooth voice replies. For explicitly requested **Alexa Notify MP3 announcements**, first configure [HTTPS audio/proxy](proxmox.md) and verify the HA Alexa notify entity.
3. Inspect actual HA sensor/event IDs and room bindings before creating any automation. Do not blindly copy generic example entity IDs; test with automations disabled.
4. Enable camera and motion features deliberately and with appropriate notice. Vision guesses can be wrong and should not be used as identity or delivery proof.
5. Create scheduled or repeating automations **disabled** initially, test single-trigger behavior and quiet periods, then enable only after validation. Avoid duplicate announcements.

The previous **Jarvis Echo Relay 0.x** package with manual `input_text` helpers, `jarvis_tablet_audio.proactive` and separate Lovelace modules is **not** a TAFA fresh-install requirement. It remains available as a [historical reference](../archive/legacy-ha-automations.en.md), not a runnable first-time recipe.

**Security:** Do not expose credentials, recordings or private text through public MP3 files or logs. Back up HA before modifying pre-existing automations.
