# TAFA App changelog

## 0.3.7 — Automatic Qwen/Piper voice routing as default
- New automatically created **TAFA Lokal** Assist pipelines select the unified Stream TTS provider instead of Piper-only.
- If Qwen is unavailable or not configured, Stream TTS falls back to Piper automatically.
- Qwen worker URL and API token must still be configured explicitly in the HA TAFA integration; no automatic scanning or exposure of private machines.
- Existing user-owned pipelines are not silently rewritten. Select **Tablet Assist Stream** as TTS engine in the existing TAFA Lokal pipeline to enable the router.
- Android Device Bridge and private dashboard remain untouched.


## 0.3.6 — CPU compatibility hotfix
- Fix failed updates on virtual CPUs without x86-64-v2: pin NumPy 1.26.4 instead of automatically selecting NumPy 2.5.5.
- Validate the resolved NumPy version and imports of Piper/Faster-Whisper during both amd64 and arm64 container builds.
- Run pip dependency checks and add a regression test for the CPU-safe NumPy pin.
- No changes to Device Bridge or the private dashboard.


## 0.3.5 — CPU speech startup repair
- Updated Piper to 1.8.0 and supplied missing Debian espeak-ng runtime/data.
- The Docker image now validates imports for both Piper and Faster-Whisper during builds.
- Ingress now distinguishes model download, model load, runtime errors and HA setup waiting for speech services.
- Add model-retry action and a full startup traceback in App logs, without logging speech or transcripts.
- Device Bridge 1.0.0 and private dashboards are unchanged.


## 0.3.4 — Release-candidate documentation correction
- Clarifies that unchanged Device Bridge 1.0.0 emits wake events only; a separate microphone-capable Assist client must capture the spoken question.
- Ingress guidance no longer asks users to select a pipeline inside Device Bridge.
- No Android/APK modifications.


## 0.3.3 — Release-candidate hardening
- Add Device Bridge configuration to the public TAFA sidebar (mute, wake words, room names).
- Add real HA Core integration checks for native relay, multiroom, camera and motion.
- Add mocked Core API and Ingress CSRF tests; supervise the CPU speech subprocess.
- Versioned backend integration 0.4.1; Android Device Bridge 1.0.0 unchanged.

 
## 0.3.2 — Unified backend release candidate
- One integrated Home Assistant component; CPU Piper and Faster-Whisper run inside the App container.
- Automatic Core config flow and TAFA Lokal pipeline creation, without replacing existing pipelines.
- Safe, checksum-verified managed upgrades with rollback copies; HACS and manual installs untouched.
- Administrator-only Ingress Control Center, model and HA setup status, bounded in-memory CPU speech APIs.
- Android Device Bridge and the private TAFA dashboard are unchanged.
- Clean HA OS and physical Android multiroom/audio tests are still required before a stable designation.

## 0.1.1 — Early developer preview
- Initial HA App bundle and guarded installation.

## 0.1.0 — Initial prototype
- HA Apps repository, Ingress setup page and public integration packaging.
