# TAFA App changelog

## 0.3.30 — Dashboard-only initial HA configuration
- New HA integration 0.4.15 allows an explicit dashboard-only first setup without a reachable Piper /health endpoint. Normal voice setup continues to require a healthy Piper service.
- TAFA Dashboard and its admin-controlled HA storage mappings can now be initialized while the separate Proxmox/CPU speech server is configured later.
- No existing automations or Jarvis Assist pipelines are changed.


## 0.3.29 — built-in, portable TAFA Dashboard replaces the Voice Center landing
- The real household dashboard was inspected via HA MCP. Instead of publishing its private 20-module Kiosk resources and site-specific entity IDs, the portable TAFA Home Dashboard v0.2 visual architecture (energy, solar, battery, EV, heating, heatpump, fuel, appliances, cameras, waste, shopping, weather, lights and Assist) now ships directly inside the HA custom integration.
- HA integration 0.4.14 opens TAFA Dashboard as its default sidebar panel. The former Voice Center continues inside Dashboard → Sprachdienste, retaining its device controls, learning, room announcements and pairing tools.
- Administrator-editable Dashboard settings, section selection and per-role entity pickers are persisted centrally via Home Assistant's Store helper and admin-only WebSocket command. No hard-coded private entity IDs, external JavaScript resources, YAML edits or automation changes.
- Built-in SVG icon, DE/EN UX, theme/fullscreen and built-in Home Assistant entity detail controls remain available. The bundle includes all dashboard JavaScript and is mirrored between standalone and App-managed integrations.
- Legacy Jarvis dashboards and automation references are left unchanged for a gradual, testable migration.


## 0.3.28 — reconcile Wyoming roles at final Supervisor write
- Fix duplicate CPU/GPU Wyoming STT validation that could still fail after a confirmed JSON import: the Supervisor App options are re-read inside the last write function, so role reconciliation must also happen there, on the freshest values.
- Preserve the imported GPU/Proxmox role; remove only its exact duplicate in the opposite role. Unrelated and genuinely separate CPU/GPU STT entities remain unchanged; manual settings still reject duplicate assignments.
- Show pre-existing role cleanup in the import confirmation preview, add actionable guidance, and test configurations that change between preview and persistence.


## 0.3.27 — automatically resolve conflicting CPU/GPU Wyoming mappings
- JSON import assigns the verified Wyoming STT entity to the role of the imported worker (GPU) or speech CT (CPU). If an old opposite-role field points to that exact same entity, TAFA clears only that stale field; distinct providers remain intact.
- Validate the repaired proposed options before HA configuration, even if the current saved options have a conflicting CPU/GPU STT pair. This also applies to deferred HA entity resolution and import resume after HA Core restarts.
- Integration 0.4.13 no longer picks the explicitly selected GPU Wyoming as CPU merely because it is the only provider; initial migration does not resurrect a CPU alias for the GPU.
- TAFA Lokal external Proxmox setup does not substitute GPU Whisper as its CPU fallback provider.


## 0.3.26 — recover stale Wyoming mappings even when HA still runs old code
- Compatibility retry for HA Core processes still running integration 0.4.11: when the backend reports exactly "Previously mapped integration missing; review first", TAFA retries the approved manifest after dropping only the stale recorded mapping(s).
- Never retry for connectivity errors, invalid JSON, missing backend or other provisioning failures; keep existing unrelated HA entries untouched.
- On success, the importer saves the newly returned Wyoming/Ollama entry IDs so the next import is clean. The installed integration 0.4.12 still provides the permanent fix; HA Core restart is recommended to load that version.


## 0.3.25 — recover deleted Wyoming and explain JSON setup errors
- Re-importing a previously approved GPU/Proxmox JSON now recreates a Wyoming integration that was explicitly deleted in Home Assistant; a stale mapped config-entry ID no longer blocks provisioning.
- Also recover deleted previously linked Ollama integration entries when an enabled server is reachable; never overwrite or delete unrelated integrations.
- Display bounded Home Assistant provisioning error details (for example, Wyoming cannot_connect) instead of only provision_failed, so connection issues can be diagnosed without server logs.
- Keep the same private manifest validation and device-ID mapping; no worker JSON update required.


## 0.3.24 — import-first setup, resumable HA provisioning and Android-brand UI
- Fresh installations start in setup mode without loading or downloading local CPU speech models. Existing installs keep their saved local/external source; importing GPU JSON enables CPU fallback, while Proxmox JSON selects external speech.
- Administrator-approved JSON import provisions Wyoming/Ollama when possible. If HA Core needs to load the newly staged custom integration, the approved import is queued and can optionally trigger an explicitly authorized Core restart; provisioning and delayed entity mapping resume afterwards.
- TAFA Lokal is created when its Assist entities are available, and the Control Center shows an actual read-only readiness check and links to HA voice assistant selection. No default assistant is changed.
- Control Center and HA Sprachzentrale both display the original teal/mint Android launcher vector as a shared SVG asset. No Android binary modifications.


## 0.3.23 — JSON worker and speech CT setup import
- Add a compact JSON file/paste wizard to Settings: preview first, explicitly confirm changes, and store a stable worker/CT identity for future IP reimport.
- Provision Home Assistant Wyoming and optional Ollama through a separate admin-only TAFA backend command; preserve unrelated integration entries and existing Assist pipelines. Never auto-download an Ollama model.
- Apply imported IPs and discovered STT/conversation entity IDs to Supervisor's existing App options, without creating a parallel settings store. A Home Assistant Core restart may be needed after installing the new backend.
- Worker 2.2.4 exports `tafa-worker.json`; Proxmox installer exports `tafa-speech.json` with the same schema.


## 0.3.22 — redesigned Control Center with clear tabs and refreshed colors
- Redesigned the admin-only Control Center with four accessible responsive tabs: Overview, Settings, Connections, Maintenance & help, replacing the long scrolling page.
- New restrained slate/navy/teal palette, light/dark modes, compact status dashboard, distinct endpoint cards, keyboard-accessible navigation and reduced-motion support.
- Preserve settings form contents when switching tabs, retain the selected tab after submitting forms and when switching languages; keep all content usable without JavaScript. Local CSS and JS use a restrictive same-origin content security policy.
- Existing App options, GPU worker, Home Assistant integration, Android Bridge and speech routing remain unchanged.


## 0.3.21 — endpoint-aware setup diagnostics
- Show safe read-only connection status beside configured private Piper, Qwen, MP3 and GPU-Whisper TCP addresses; do not confuse an open Wyoming port with successful GPU transcription.
- Display the last actual Home Assistant STT router backend (GPU versus CPU) when available; show an optional GPU Whisper host suggestion derived from the configured private Qwen IP.
- Explain that Ollama URL belongs in HA Devices & services while TAFA only selects its conversation entity. Public HTTPS audio links are never probed by the App.
- Existing Supervisor option storage, integration and Android application unchanged.

## 0.3.20 — one guided Control Center settings page
- TAFA Control Center now provides one bilingual settings form for speech mode, Piper/Whisper, GPU Qwen, Ollama agent, speech routing, Alexa and optional advanced mappings. The previous separate Wyoming picker becomes part of this page.
- Saving writes only validated changes to the existing Supervisor-managed App options; no second configuration store or changes to user Assist pipelines. Restart TAFA to apply. The native Home Assistant App Configuration stays as an advanced recovery editor.
- All fields are checked server-side, rendered with HTML escaping, and protected by Ingress authorization and CSRF. Add integration tests for settings preservation and validation.
- HA integration, GPU Worker and Android Device Bridge unchanged.

## 0.3.19 — Wyoming picker Docker startup hotfix
- Bundle `wyoming_picker.py` so the TAFA App does not crash with `ModuleNotFoundError` on startup after 0.3.18.
- Check the import during the container build and test that all local Python server imports are copied into the image.
- Existing configuration, HA integration 0.4.9, GPU Worker and Android Device Bridge unchanged.

## 0.3.18 — live Wyoming STT dropdowns in the Control Center

- New admin-only **TAFA Control Center → Automatically discover Wyoming STT** panel lists currently registered enabled `stt.*` entities directly from Home Assistant. Explicitly assign the CPU Proxmox and GPU Windows Whisper roles via dropdown instead of typing IDs.
- Save persists the selected distinct entity IDs in the Supervisor-managed TAFA App options without changing unrelated options; restart the App once to synchronize the HA routing. Disabled, stale, unregistered and non-Wyoming entries cannot be selected for a new mapping.
- Displays a clear missing-Wyoming explanation and setup link. Built-in HA Apps Configuration keeps its existing backward-compatible string fields because its static schema cannot dynamically populate choices.
- The GPU Worker 2.2.2 connection TXT documents the companion Wyoming, Ollama and TAFA setup steps; no existing Android or HA service endpoints change.

## 0.3.17 — first Ollama question no longer blocked
- Fix TAFA conversation router incorrectly rejecting Home Assistant ConversationEntity state `unknown` (the normal state before its first message). The first voice question now reaches the selected Ollama agent.
- Hardware profile `cpu` selects Piper TTS and must not independently disable an otherwise configured Ollama text agent.
- A missing/self-referencing agent and `unavailable` state continue to report setup/unavailability; no silent network probing or automatic model downloads.
- App 0.3.17 bundles integration 0.4.9; Android Device Bridge APK remains unchanged. Tested with isolated availability regressions.



## 0.3.16 — complete native Assist pipeline readiness for Proxmox users
- External Proxmox mode no longer reports `external_ready` when the `TAFA Lokal` Assist pipeline is missing; it retries configuration after Wyoming STT/entities become available (with automatic selection of a single Wyoming STT provider).
- Existing `TAFA Lokal` pipeline is preserved; an incomplete STT/conversation/TTS configuration shows `pipeline_needs_review` rather than false success.
- Under TAFA → Devices → Voice test, the setup checks the full Assist pipeline and guides enabling the optional native Android 1.0.1 capture mode (DE/EN).
- App 0.3.16 / integration 0.4.8; Android APK signing/version unchanged by this Home Assistant change.



## 0.3.15 — Audio-only device self-test works from private HTTP
- TAFA → Devices → Voice test now offers **Test speech output** with editable phrase; generate via the selected HA TTS engine (Qwen/Piper), queue to the selected authenticated tablet room, and display player-confirmed progress.
- Does not require browser microphone or HTTPS, so LAN HTTP setups can verify the full TTS-to-Android playback path after first installation.
- Full Speak once/Whisper microphone test requires trusted HTTPS. Hide its controls on insecure HTTP and show a clear explanation instead of a misleading error.
- No Android update, credentials, Home Assistant helper entities or network exposure changes.



## 0.3.14 — First-run speech and tablet playback self-test
- Built-in **TAFA → Devices → Speak once** guided microphone test reuses the user's proven room Assist implementation: browser microphone → Whisper STT → conversation → Qwen/Piper TTS → paired Android/Bluetooth audio player.
- Automatically choose TAFA Lokal when configured, allow selection of another complete STT+TTS pipeline, and show actionable errors for missing pipelines, insecure microphone origins and offline room players.
- An HA administrator may test a specifically paired tablet via a scoped room-audio API; non-admin accounts test their own room. No new HA helper entities, tokens or Android APK updates.
- Recording stops when closing/leaving the test. Full physical HA/tablet verification remains required before stable release.


## 0.3.13 — Device audio pairing in the TAFA Devices page
- Administrators can choose a non-admin HA user, assign or update an audio room, and see online/ready status for each registered tablet without developer tools or YAML.
- Each room has a separate opt-in camera permission toggle in TAFA → Devices. Camera uploads remain off by default, must be started on the tablet, and use the room account rather than an administrator token. Disabling permission revokes and clears buffered frames.
- Existing room connections and quiet-hours settings are preserved when saving the same mapping. An ownership transfer or user reassignment requires explicit administrator confirmation; never transmit tokens through the dashboard.
- Admin-protected room management API; Android Device Bridge 1.0.0 unchanged. Restart HA after updating the bundled component; new App version is 0.3.13 / integration 0.4.5.
- Confirm end-to-end on a physical HA OS and tablet before promoting to stable.

### Included Alexa Devices MP3 setup clarification
- The DE/EN description for **Alexa rooms (JSON)** explicitly recommends the **Speak** Notify entity (`notify.…_sprechen`) for Qwen MP3 playback with Alexa Devices. The **Announce** entity can play a chime without the MP3.
- Add tested example mappings and chime-without-voice troubleshooting to both setup guides and App documentation. No runtime behavior, API or existing room mappings are changed.

## 0.3.12 — Single-source App configuration
- Consolidate CPU Wyoming STT, GPU, LLM, Alexa mapping, data sources, reminders and audio preferences under **Apps → TAFA → Configuration**.
- Apply App settings automatically to existing App-owned HA integrations via authenticated Supervisor-to-HA WebSocket; no customer API tokens.
- Preserve legacy advanced settings during the first migration; subsequent App settings are authoritative. A lone Wyoming STT entity can be auto-selected.
- The Devices & services option and reconfiguration screens redirect App-managed installations rather than offering conflicting fields. Marketplace-only users retain the classic configuration flow.
- Production configurations and existing Assist pipelines are not deleted or replaced. Restart Home Assistant after the managed backend update.



## 0.3.11 — Central App setup, service diagnostics and model cleanup
- App Configuration now offers named DE/EN settings for Proxmox Piper, Qwen GPU, automatic Piper fallback, voice variant, sound profile and Alexa MP3/HTTPS.
- The built-in Ingress Control Center checks Qwen, Piper and MP3 health with bounded private-LAN requests, and shows the expected voice route; no audio is generated by diagnostics.
- App-owned Piper/Whisper cache size is visible and deletable only when bundled speech is stopped via external mode, with explicit deletion confirmation.
- First-time HA integration setup uses the configured App values. Existing user-owned integrations are not silently overwritten.
- All extra TAFA worker API tokens remain disabled. Home Assistant Supervisor authorization remains in place.


## 0.3.10 — Existing Proxmox speech-server mode
- New App Configuration fields: `speech_mode=external` and `external_piper_base=http://PRIVATE-IP:5000`.
- In external mode, bundled Piper/Faster-Whisper processes and model downloads are skipped entirely; local is the unchanged default.
- Auto-configure the TAFA HA integration only after private Piper /health is ready. Require explicit Wyoming STT configuration in HA (port 10300) before creating an Assist pipeline; no silent STT endpoint substitution.
- Ingress displays external-mode readiness and no longer offers a retry for disabled local models; Windows GPU Worker and public MP3 HTTPS proxy remain separate.
- Added tests for private endpoints, invalid addresses, no local model startup and external onboarding.

## 0.3.9 — No additional service tokens on private LAN
- Removed GPU and MP3 generator API-token fields from the new Home Assistant integration.
- Supports token-free GPU Worker 2.2.1 and token-free LAN MP3 generator.
- Added Windows BAT helpers, connection-report TXT and token-free .env templates for the worker.
- Home Assistant authentication and the public MP3-only HTTPS proxy remain unchanged.
- Private GPU and generator ports MUST NOT be forwarded to the Internet. Existing configs preserved.


## 0.3.9 — Guided first-run setup (release candidate)
- Guided TAFA-local CPU, external Proxmox, Qwen GPU routing and optional Alexa MP3/HTTPS instructions in Control Center.
- HA Options split into Speech servers & GPU, Alexa announcements & HTTPS, and Data sources & reminders.
- Public integration panel links directly to TAFA settings, with bilingual setup documentation.
- Saved GPU/MP3 keys are retained when password fields are blank; the bundled CPU processes are not yet stopped by selecting external services.
- Integration updated to 0.4.3. Android Device Bridge and private dashboard unchanged.
- End-to-end HA OS hardware verification pending.


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
