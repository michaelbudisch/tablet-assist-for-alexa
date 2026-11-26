# Security and privacy

[Deutsch](../security.md) · [TAFA setup](setup-guide.md) · [Project](../../README.md)

## Credentials and LAN-only services

- **TAFA Device Bridge** authenticates using regular **Home Assistant accounts/access tokens**. Use a separate active **non-admin account per tablet**; never commit tokens to Git, dashboard YAML, screenshots or public logs.
- The current CPU/GPU worker endpoints for Piper, Wyoming Whisper, Qwen, Vision and Ollama use **no extra TAFA worker API token**. Token-free does **not** mean public: restrict **5000, 5001, 10300, 10502, 10503, 11434**, and optional **8080/10501**, to the trusted LAN and necessary hosts through a firewall. **Never port-forward** these model APIs.
- The **TAFA App Control Center** requires authorized HA admin access. Windows worker JSON/TXT exports contain private LAN addresses and a stable device identifier, but not passwords; keep them and the local `.env` out of source control.
- **DuckDNS account tokens** and HA access tokens remain real secrets and are **not the same** as the removed TAFA worker API token.

## Microphone, camera and diagnostics

The Android microphone runs under explicit permissions and a visible foreground service. Native **Always on** mode can react to background speech and must be enabled deliberately with appropriate notice. The browser **TAFA → Speak now** page can listen automatically while visible after being enabled; it displays a **transient session transcript**, not a permanent audio archive. Check separate Home Assistant and optional third-party recording/log retention settings.

Room cameras require **both** explicit HA permission and starting the camera on the tablet. Image-based motion/Vision descriptions can be wrong and are not reliable identity recognition. Inform others who share any room with microphones or cameras.

## Alexa, HTTPS and remote access

Ordinary conversation audio uses **Android → Bluetooth → Echo** and requires no public audio domain. Optional **Alexa MP3 announcements** use Amazon services and public **HTTPS file delivery** for randomly named short-lived audio files. Do not send confidential messages through them. Public proxy routes must serve **only** required audio files, never speech-generator, Wyoming, Vision or Ollama APIs.

Optional local [HTTPS/split DNS](local-https.md) helps meet secure-browser microphone requirements but **does not close an existing public HA proxy route**. Protect public HA logins with strong credentials, MFA and reviewed network rules; never expose DNS TCP/UDP 53.

TAFA updates do not migrate or change existing household automations or privacy policies. Back up HA and independently verify security before enabling new public proxy, camera or voice features.
