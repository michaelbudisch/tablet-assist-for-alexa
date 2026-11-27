## HA integration 0.4.66 · Near-tablet presence
- Independent authenticated device channel and occupancy entity per enrolled tablet. Eight-second expiry; no coupling to image motion, wakeword or greetings.
- Android 1.2.9 supplies local front-camera results with adjustable threshold and exit delay. Public integration and App installer ship the same sensor implementation.

## TAFA App / HA integration 0.4.62 — Contain internal light pulses within sphere
- Both gentle transition rings expand out from the center but fade before reaching the globe's edge; removed the former overshoot to 133% of the sphere's radius.
- Multi-hop network light packets, their trails and flashed-node halos are clipped to the sphere silhouette; they no longer extend into the surrounding scene.
- Separately rendered shooting stars still orbit outside the sphere, unaffected by the inner clip. Manual 3D rotation, momentum, staged reply panels, instant voice state reporting and automations remain unchanged.

## TAFA App / HA integration 0.4.61 — Multi-hop node signals and subtle radial pulses
- Closer match to the reference HD video (around 39–40 s and 68–70 s): one restrained expanding circular pulse on listening→processing and a second on processing→speaking, each with a faint echo. Repeated updates in the same phase never spawn duplicate rings.
- Signal packets now traverse **connected 6–8-node routes along the actual 3D globe graph** instead of isolated edges. Each reached vertex flashes briefly and the packet continues through the next connection. Packets reverse along their route at the end rather than jumping between disconnected paths.
- Luminous node arrivals and short multi-edge trails are more legible. Listening uses cyan, thinking brighter white-violet, and output a soft silver-lavender palette.
- Caps active 3D paths at 14 on Android and 23 on desktop. Preserves instant native voice state reporting, manual globe drag, comets, response panels, automations and entity mappings.

## TAFA App / HA integration 0.4.60 — Reference-style sphere lighting and materialized replies
- Idle: sparse turquoise curved orbital shooting stars over a quiet silver 3D node network.
- Listening: bright cyan core and directional light packets running along real projected network edges, lighting selected nodes.
- Processing: luminous pearl-white/violet core, more and faster white orbital streaks (including inner paths), staggered white node sparks. Speaking: softer silvery-lavender packets and trails.
- Light and orbit modes blend continuously without resetting sphere rotation on rapid native phase changes.
- Reply panels unfold from a thin connector light line below the sphere: traced border, expanding glass surface, staggered heading/message and an optional non-verifying contextual icon. Streaming text updates do not restart the panel; search result lists and camera notes remain supported.
- Additional 3D lights are bounded on older Android devices. Native wake telemetry, unrestricted manual rotation and existing HA automations remain unchanged.

## TAFA App / HA integration 0.4.59 — Smooth Ambient speech transitions
- Listening, processing, speaking and idle now blend continuously across color, glow, pulse, motion, shooting stars and status labels. Rapid transitions retarget rather than restart the visualizer.
- Prevents rotation jumps by integrating angular velocity instead of multiplying absolute elapsed time by a changing phase speed. Manual 360° dragging and soft inertial handoff remain.
- Targets about 30 FPS on Android and up to 60 FPS on desktop, maintaining conservative tablet canvas resolution.
- Native instant phase reporting, existing automations and entity assignments remain unchanged.

## TAFA App / HA integration 0.4.57 — Immediate native voice phases
- Android Device Bridge 1.2.5 source pushes wakeword and Assist states to the existing authenticated HA device telemetry API when each state changes, not only at the periodic 12-second full sync. An independent coalescing worker preserves the initial `detected:` event and keeps audio/UI threads unblocked.
- Ambient now maps WebSocket authentication and connection to the listening phase, transcription/thinking to processing, and buffering/playback to speaking.
- Integration preserves the last wakeword timestamp across telemetry reports and updates it on native detection, without firing duplicate legacy wake events.
- Signed Android 1.2.5 APK is not published yet; the original signing key is required to install the updated app over 1.2.4.
- No changes to automations or configured sensor bindings.

## TAFA App / HA integration 0.4.56 — Unrestricted vertical globe rotation
- Removed the former ±1.2 radian vertical pitch clamp from both pointer dragging and inertial spin.
- The Ambient sphere can now complete unlimited 360° upward or downward revolutions with 3D-anchored sensor labels rotating along with it.
- Immediate smooth auto-spin handoff, comets, touch/mouse gestures, and tap-to-reveal Day View remain unchanged. No automations or sensor bindings modified.

## TAFA App / HA integration 0.4.55 — Smooth inertial handoff after manual rotation
- Removed the 30-second delay following globe drag release.
- The globe and its anchored 3D sensor labels continue rotating in the next animation frame. Drag momentum fades out smoothly while automatic orbit speed ramps back up.
- Releasing a stationary long press also resumes auto rotation immediately. Touch/mouse interaction, shooting stars, hidden Day View button, module isolation, and automations are unchanged.

## TAFA App / HA integration 0.4.54 — Corrected globe drag hit area
- The grab cursor was visible over the whole Ambient canvas, but dragging previously started only inside a smaller circular hit test. The entire canvas is now draggable, matching the displayed cursor on desktop and tablet.
- The early-movement drag fix (6 px), stationary long-press activation (280 ms), attached 3D sensor anchors, and tap-to-reveal Day View remain in place.
- No entity mappings, automations, or other Lovelace dashboard tiles changed.

## TAFA App / HA integration 0.4.53 — Reliable press-and-drag globe rotation
- Fixed a gesture cancellation bug: v0.4.52 aborted rotation when a pointer moved more than 11 px before the 280 ms hold timer elapsed. Movement of 6 px now immediately activates manual 3D rotation.
- Holding still for 280 ms before dragging remains supported. Mouse and touch share pointer handling; the globe and projected 3D sensor anchors rotate together.
- A short tap still reveals Day View, and automatic rotation pauses for 30 seconds after drag release before resuming smoothly. Existing modules, automations, and Lovelace configuration remain unchanged.

## TAFA App / HA integration 0.4.52 — Press-and-drag Ambient globe
- Press and hold the globe for 280 ms, then drag horizontally or vertically to rotate its 3D mesh and the attached six sensor anchors together. Touch and mouse share pointer handling.
- Auto-rotation stays paused for 30 seconds after release, then resumes smoothly from the chosen orientation without jumping. A short tap still reveals the day-view control, whereas dragging leaves it hidden.
- Ambient shooting stars, sphere line weight, speech phases, and HA automations remain unchanged. Frontend imports use `?v=0.4.52`.

## TAFA App / HA integration 0.4.51 — Tap to reveal Ambient exit control
- The Ambient day-view button is hidden initially on desktop and Android. A tap or click on the Ambient stage reveals it; it automatically hides after six seconds of inactivity. Keyboard Enter/Space also reveals the control.
- Visual effects, speech interactions, integration/private module isolation, and normal day mode remain unchanged. Cache-busted import URLs use `?v=0.4.51`.
- No automations or entity associations changed.

## TAFA App / HA integration 0.4.50 — Consistent minimal Ambient header
- Night mode now hides the normal dashboard header and action buttons on desktop as well as Android. A single `☀ Day view` control inside Ambient mode allows returning to the normal dashboard.
- Existing day-mode navigation, shooting stars, globe, sensor projections and voice phases remain intact. Private/public Ambient namespaces stay isolated. New cache-busted `?v=0.4.50` URLs.
- No automations changed.

## TAFA App / HA integration 0.4.49 — Isolated Ambient module
- The public TAFA integration now uses its own `tafa-ambient.integration.v1` symbol namespace so its renderer cannot overwrite private Hauszentrale Ambient mode.
- Removed tablet diagnostic overlays from the normal night view; standalone WebView test remains separately accessible.
- Private Hauszentrale uses its own `privateAmbient` registry and ready event. Frontend imports are cache-busted with `?v=0.4.49`.
- Existing sphere visuals, shooting stars, and HA automations remain unchanged.

## TAFA App / HA integration 0.4.48 — Android WebView full-screen and diagnostics
- Ambient mode on Android now uses viewport-fixed positioning instead of inheriting the Home Assistant dashboard card grid width.
- Added a built-in exit button for returning to the day view and tablet-only frontend version, viewport, layout width and Canvas diagnostics.
- A private standalone `/local/tafa/ambient-webview-test-v0.4.48.html` page distinguishes WebView issues from dashboard layout issues. The private resources use `?v=0.4.48` and unique filenames.
- Globe, shooting stars, automations, and configured entities are unchanged.

## TAFA App / HA integration 0.4.47 — Organic shooting stars around Ambient globe
- Replaced permanently rendered surrounding arcs with short-lived 3D orbiting comets, each with a glowing head and short fading trail.
- Spawn times, orientations, distance, speed, brightness, and lifetime are varied. Existing sphere mesh, line strength, idle calm, and active-voice animations remain unchanged.
- Cache-busted frontend imports (`?v=0.4.47`) and updated private dashboard version manifest.
- Existing automations and sensor associations remain unchanged.

## TAFA App / HA integration 0.4.46 — Frontend cache diagnostics
- Bumped version query parameters for the distributed dashboard and frontend module imports to `?v=0.4.46`.
- The private Hauszentrale dashboard now loads separate versioned `0.4.46` files and has an optional runtime update guard. It detects when a previously registered CustomElement is still running stale code, offering an explicit CacheStorage clear and full-document navigation. Private code is not shipped here.
- No automation or settings changes.

## TAFA App / HA integration 0.4.45 — Versioned frontend modules
- Dashboard, ambient visualizer, and supporting modules use `?v=0.4.45` import URLs; increment them for each frontend release to invalidate stale browser and Android WebView caches.
- Private HA dashboard main and ambient scripts are now served as versioned `/local/tafa/` files (versioned filename and `?v=`). Private dashboard code is intentionally not published to this repository.
- Existing Home Assistant automations and entity mappings remain unchanged.

## TAFA App / HA integration 0.4.44 — Calm idle state for Ambient mode
- Idle globe now only rotates gently: no vertex warping or size pulsing; orbiting sparkles are subdued.
- Enhanced motion and pulsing are restricted to detected wakewords and actual Assist listening, processing or playback, not the always-armed native wakeword monitor (`listening: hey_jarvis`).
- Existing HA automations, dashboard layout and entity mappings are untouched.

## TAFA App / HA integration 0.4.43 — Organic 3D Ambient view and tablet layout
- Replaced the uniform globe with a non-uniform 3D particle network, drifting lights and partial orbit arcs. Six sensor values follow depth-projected vertices as the globe rotates, including perspective scale and fading.
- Full-width tablet portrait/landscape ambient layout, independent of the normal dashboard sidebar. Cache version updated for the Android WebView.
- Existing automations and entity mappings are preserved.

## TAFA App / HA integration 0.4.42 — Safe, optional Ambient mode
- The ambient night visualizer is now loaded optionally, with a fallback that never blocks the dashboard when unavailable.
- Protected module loading and clean animation lifecycle. Existing TAFA/Jarvis event responses can appear in a bottom animated panel, without altering automations.

## TAFA App / HA integration 0.4.41 — Ambient night dashboard
- Optional animated night view featuring a rotating connected-particle sphere, large clock, dynamic HA sensor metrics and voice-aware color changes.
- Header action toggles the ambient view without replacing normal daytime layout, voice settings or automations.
- TAFA Assist events display a contextual animated answer/search panel beneath the sphere. Native device mic/wake sensor values drive listening states when available.
- Lightweight canvas animation shuts down when switching views. Existing private kiosk dashboard can use the same shared visual module.

## TAFA App 0.3.35 / HA integration 0.4.20 — no duplicate camera entities during migration
- Register TAFA camera/motion entities only if the TAFA camera relay is active, preventing null relay exceptions while preserving the separately running legacy camera integration. Audio/microphone services remain TAFA-owned.

## TAFA App 0.3.34 / HA 0.4.19 / Android 1.0.2 — direct audio only
- One conversation transport: native Android → HA Assist TAFA Lokal → authenticated room-scoped Android player → Bluetooth. Follow-up limits per device configurable from Home Assistant (0–100 or unlimited). Dashboard microphone control and safe multiroom room picker. Legacy room pairing read-only migration.

## TAFA App 0.3.33 / integration 0.4.18 — voice services styled and embedded
- The TAFA dashboard navigation now opens voice management within the existing dashboard layout, preserving its header, clock, bottom/side navigation and teal dark theme. The standalone view remains available by direct link and shares its new visual design. No automations or existing voice pipelines changed.

## TAFA App 0.3.32 / integration 0.4.17 — remove duplicate dashboard toolbar
- Use the dashboard's native navigation and settings gear for Voice services and HA-stored configuration instead of an additional always-visible toolbar. Subviews retain contextual Back/Save/Cancel controls.

## TAFA App 0.3.31 / integration 0.4.16 — isolated dashboard custom elements
- Namespace the built-in TAFA panel card and editor separately from an existing TAFA Home Lovelace preview. Preserve both UIs, avoid global custom card registration collision, and update frontend cache version.

## TAFA App 0.3.30 / integration 0.4.15 — dashboard-first setup
- Explicit dashboard-only setup of the HA integration before a speech server is ready. Keep the normal Piper health requirement for voice-enabled setup and preserve all automations.

## TAFA App 0.3.29 / integration 0.4.14 — portable TAFA Dashboard as the integration panel
- Ship a portable, modular, entity-bindable home dashboard based on the local TAFA Home preview and original Kiosk visual language, replacing the Voice Center landing in the sidebar. Existing voice-management features remain available in the Voice services subview.
- Store admin-approved dashboard bindings across devices via Home Assistant Store; avoid publishing home-specific private entities or modifying automations and existing Jarvis dashboards.

## TAFA App 0.3.28 — reconcile CPU/GPU Wyoming at final import save
- Fix stale CPU/GPU STT duplicates after confirmed JSON import by comparing against freshly loaded Supervisor options in the last write operation. Show prospective cleanup and preserve genuinely separate providers. Manual settings remain strict.

## TAFA App 0.3.27 / HA integration 0.4.13 — distinct CPU/GPU Wyoming
- Confirmed JSON imports reconcile a conflicting old opposite role without touching distinct STT providers. Future HA provider discovery uses the same rules. Integration 0.4.13 will not mis-assign the configured GPU provider as CPU merely because it is the only Wyoming endpoint.

## TAFA App 0.3.25 / integration 0.4.12 — deleted integration recovery
- Re-importing an approved manifest now recreates explicitly removed Wyoming/Ollama config entries instead of failing on their stale stored IDs; only the approved endpoint is used. Show HA flow errors when setup cannot reach a service; no worker re-installation required.

## TAFA App 0.3.24 / integration 0.4.11 — import-first and shared Android branding
- Fresh installations wait for confirmed worker/CT JSON before starting local model downloads; existing deployments retain their selected mode. Automatic entity resolution and Assist-pipeline continuation after import.
- Add read-only TAFA Lokal readiness diagnostics and direct voice assistant selection link; never overwrite HA defaults. Both Control Center and Voice Center display the shared Android two-color launcher vector.

## TAFA integration 0.4.10 — approved device manifest provisioning
- Adds admin-only HA setup for imported GPU/Proxmox manifests: matches/reconfigures Wyoming and provisions compatible Ollama connections and existing-model conversation agents while preserving unrelated entries and existing Assist pipelines.

## TAFA App 0.3.23 / GPU Worker 2.2.4 — confirmed JSON import
- Introduce JSON export from GPU Worker and Proxmox speech CT with stable device IDs, and a preview/confirm import in TAFA Control Center. Home Assistant provisions Wyoming and supported Ollama agents without overwriting unrelated integrations or downloading unknown models. Reimport the same device ID after IP changes.

## TAFA App 0.3.21 / GPU Worker 2.2.3 — endpoint status and concise connection TXT
- The unified Control Center now shows read-only reachability for configured Piper, Qwen, GPU-Whisper Wyoming TCP and MP3 endpoints and the last HA STT backend when available. It suggests GPU Whisper IP from Qwen URL when both run on the same LAN computer.
- GPU Worker TXT lists only its own known IP endpoints and exact Home Assistant/TAFA destinations (DE/EN); no extra instructions. Public HTTPS addresses are not automatically probed.

## TAFA App 0.3.20 — unified settings interface
- Settings are now configured from one grouped, bilingual TAFA Control Center form. Native HA App Configuration is an advanced fallback on the same Supervisor-managed options, not another store.
- Existing configurations preserved, validated and stored; restart TAFA to apply. CPU/GPU Wyoming selection is included in the central form.
- External speech mode can still be preselected through native App Configuration before the very first launch to avoid downloading bundled models.

## TAFA App 0.3.19 — fix Docker startup
- Include the missing `wyoming_picker.py` in the Docker image and verify it imports during the build.
- Regression guard prevents omitting local TAFA server modules. No existing configuration, HA integration, Android app or GPU changes.

## TAFA App 0.3.18 / GPU Worker 2.2.2 — guided Home Assistant setup
- Generated GPU connection TXT now provides complete bilingual Wyoming GPU/CPU STT, Ollama conversation, Qwen TTS and precise TAFA field mapping.
- TAFA Control Center discovers registered Wyoming STT entities and offers explicit CPU/GPU dropdown assignment. Save persists only these two choices in the App options; restart the App to synchronize.
- Existing backend configuration, Android APK, GPU endpoints, LAN-only policy and CPU fallback are unchanged.

## TAFA App 0.3.17 / integration 0.4.9 — first Ollama conversation fix
- `unknown` is the normal HA ConversationEntity state until its first message, not proof of a disconnected LLM. Allow the first voice turn to reach the configured agent.
- CPU/Homeserver hardware profile controls TTS routing, not whether a configured HA conversation agent may respond.
- Preserve missing/unavailable/self-reference checks, update bundled integration and add isolated regression tests; no Android APK changes.

## TAFA App 0.3.16 / integration 0.4.8 — native Android Assist readiness
- In external Proxmox mode, retain a pending setup status until TAFA Lokal Assist pipeline exists; never report ready before the required HA entities and pipeline are registered.
- Incomplete existing TAFA Lokal pipelines are preserved and identified as needing review.
- TAFA Devices guides the optional Android 1.0.1 native microphone setup, clarifying full STT, conversation and TTS requirements.

## Integration 0.4.0 — unified backend candidate
- Guided Proxmox installer, recovery wizard and CT console are fully English. Users can choose a validated container hostname (default `tafa-voice`); existing/running CT hostnames are unchanged.
- Single TAFA integration with native Device Bridge API compatibility, multiroom services, camera/motion and opt-in vision. CPU STT can use the local TAFA App. The existing Android APK is unchanged.
- Release acceptance: automated checks plus clean HA OS installation and real-audio testing required before marking stable.

# Changelog

## TAFA App 0.3.15 / integration 0.4.7 — HTTP-compatible speech output check
- New editable **Test speech output** action in TAFA → Devices → Voice test, sending actual Qwen/Piper audio through the authenticated paired Android room and reporting playback states.
- A trusted HTTPS context remains required for browser microphone testing, but not for the audio-only TTS test. On HTTP, avoid mounting the unsupported microphone test UI.
- No Android, secrets or network exposure changes.



## TAFA App 0.3.14 / integration 0.4.6 — built-in spoken setup test
- TAFA → Devices includes the proven "Speak once" browser microphone → Whisper → Assist → Qwen/Piper → paired tablet audio test, with automatic pipeline selection and a clear secure-context requirement.
- Authenticated room user or administrator-scoped selected device, with no token in the dashboard, no duplicate HA helper scripts and no Android APK update. Capture stops on closing the view.


## TAFA App 0.3.13 / integration 0.4.5 — tablet room pairing
- TAFA → Devices now combines wake-device controls and admin-only Multiroom audio room pairing, selectable non-admin HA user, room ID and live online/ready state.
- Opt-in per-room camera access is managed in the same panel, disabled by default, and cleared on revocation; Android still requires explicit capture start and uses the room user token.
- Secure, explicit ownership transfer with confirmed account reassignment; existing player sessions, quiet-hours and audio room settings remain intact when unchanged.
- No YAML, duplicate installation or new token handling in the HA dashboard. Android app 1.0.0 unchanged.



## TAFA App 0.3.12 / integration 0.4.4 — single configuration source
- Apps → TAFA → Configuration is the source of truth for App-managed installations; all integration options and optional data source/room mappings are represented there.
- Admin-only WebSocket sync updates existing App-managed integration entries, avoiding duplicate setup under Devices & services. First migration preserves advanced options when newly added App fields are blank.
- Marketplace users remain configurable through the normal HA integration; existing HA Assist pipelines and legacy deployments are preserved.



## Unreleased — guided combined Proxmox CT installer
- Proxmox CT creation now uses native interactive `pct create --password` in the guided combined and separate-CT installers. The root password is entered privately during installation, never passed in the script's command arguments.

- New optional `proxmox/quick-install.sh` script creates a single new unprivileged Debian CT after confirming free CT ID, storage, network, resources, optional GPU worker and Alexa hostname.
- Piper, Wyoming Whisper, MP3 generator and Nginx share the new guest. Temporary audio port 8080 binds to loopback only; generator port 5001 must remain private LAN only.
- Persistent console status via `tafa-info`, guided HTTPS via `tafa-setup` and periodic login banner.
- Existing CTs, VMs, proxy sites, router ports and TLS certificates are unchanged. A physical PVE end-to-end test is still required.


## TAFA App 0.3.11 — Central onboarding, diagnostics and cache cleanup
- Translated HA App options for Proxmox, Qwen/Piper fallback, voice, and Alexa MP3.
- Ingress read-only connection diagnostics for GPU, Piper and MP3 without generating audio.
- Explicit safe deletion of TAFA-owned downloaded CPU models when external mode is active.
- App configuration seeds new HA integration entries; existing entries remain user-controlled.


## TAFA App 0.3.10 / integration 0.4.3 — Proxmox-only speech option
- Added opt-in external speech-server mode in the App Configuration to avoid duplicate local Piper/Whisper model downloads when using a trusted Proxmox guest.
- Existing local setup remains the default; external Wyoming STT and Assist pipeline are selected explicitly in Home Assistant.
- No change to GPU Worker 2.2.1, Android Device Bridge 1.0.0, Nginx proxy or the private dashboard.

## TAFA integration 0.4.3 / App 0.3.9 — token-free LAN endpoints
- No additional GPU or MP3 generator API keys in TAFA options or LAN worker requests.
- GPU Worker 2.2.1 offers token-free Qwen, Vision, Diagnostics and optional Ollama gateway.
- Token-free Proxmox MP3 generation; public HTTPS audio access remains read-only and restricted to short-lived opaque files.
- Home Assistant authentication, Android Device Bridge and private dashboard remain unchanged.
- Restrict GPU/generator ports to trusted LAN; never port-forward them.


## TAFA unified integration 0.4.3 / App 0.3.9 — guided onboarding
- Focused integration options for local/Proxmox speech servers, optional Qwen GPU routing and Alexa MP3/HTTPS.
- App Control Center now provides clear three-step setup with port hints; concise DE/EN guides.
- Data-source settings and existing credentials preserved, Android Device Bridge unchanged.
- Automated tests and HA OS hardware verification required before stable release.


## TAFA unified integration 0.4.1 — release candidate
- Unified native device and multiroom management in the public TAFA panel.
- Enhanced HA runtime, automatic pipeline and Ingress regression checks; App 0.3.4 with CPU speech-process recovery.
- Device Bridge APK 1.0.0 and private household dashboard remain unchanged. Stable release pending clean HA OS/hardware confirmation.


## TAFA Apps preview 0.1.0
- Added an experimental HA OS app repository, bundled public integration installer and administrator-only Ingress setup page. No private dashboard or automatic migration; Marketplace base integration remains 0.3.1.

## Unreleased — Marketplace backend consolidation plan
- Clarified the current installation boundary and the single-domain target; Android branding updated to TAFA Device Bridge 1.0.0. Private dashboard remains excluded. No new integration release or backend migration is claimed.

## Unreleased — TAFA kiosk room audio compatibility
- Reusable TAFA integration fix: assigned room players remain discoverable when an existing room user later receives admin privileges. Unassigned users retain their legacy audio route.
- Standalone room card and Multiroom backend remain unchanged; dedicated non-admin room accounts remain the default.
- German/English integration guidance and Node regression tests run via GitHub Actions; private kiosk source is not published.

## Unreleased — optional local HTTPS / split DNS
- Added optional Debian/Proxmox LAN DNS setup for an existing NGINX/Certbot proxy without changing HA, vhosts, certificates or router ports.
- German/English Android microphone, offline use, validation and rollback guides with input/syntax tests.
- No new product or APK release; `VERSION` remains at the last released version.


## Multiroom camera-aware vision — backend 1.7.1
- The administrator proactive vision check can now select a consented room camera by `room`, instead of relying on the legacy global camera frames.
- Room-scoped `jarvis_echo_relay_detection` events include the originating room; stale/replaced sessions are rejected and legacy single-device checks are unchanged.
- German/English migration instructions for wiring the prepared office greeting and preventing duplicate announcements.
- Requires updating the HA custom component and reloading the integration; no automatic installation is performed.


**English** | [Deutsch](CHANGELOG.de.md) · [Project overview](README.md)

## Multiroom — backend 1.7.0 / Android 0.6.0 / room cards 0.2.0 and 0.1.1

- Separate authenticated room audio and optional JPEG camera/motion entities; explicit consent, memory-only images, no identity tracking.
- Room provisioning, quiet hours, targeted announcements, area-aware Assist and better status errors; generic kiosk audio adapter, private dashboard excluded.
- Published signed Android 0.6.0 APK unchanged. DE/EN setup guides include HTTPS and matching room account.
- One real tablet and automated two-room checks passed; concurrent physical two-tablet and fresh-install validation outstanding.

## Native HA automation preview — optional card 1.3.0

- Structured detection schema supports coarse apparent presentation labels, with unknown and invalid-result guards.
- Optional portable family helpers, speech request/ack bridge, and native greeting automation package.
- Private kiosk speech and greeting tested on an existing installation; standalone card deployment remains a preview.

## Echo Relay proactive actions — backend 1.6.0 / worker 1.9.0 / card 1.2.0

- Opt-in motion-triggered structured people/dog detections, coarse adult/child/unknown appearance and no identity or gender inference.
- Repeatable all-hours test mode with adjustable cooldown; morning window and persisted daily guard in normal mode.
- HA forecast-based rain advice, optional fixed greeting name, single-dashboard native streaming playback and yes/no daily-overview follow-up.
- Explicit category/script selection and a detection event for native HA automations. Offline/busy/stale/uncertain checks skip actions.
- Shared German/English Lovelace settings, portable motion automation and isolated worker/HA/browser coverage. Existing APK 0.5.0 is unchanged.

## Lovelace settings 1.1.0 / control panel 1.6.0

- Shared theme-aware settings with accessible voice/audio, display/cameras, AI/performance and history/diagnostics tabs.
- Inline model/helper radio choices preserve pending selections during live HA updates and show rejected saves at the field.
- Standalone card gains persisted microphone/conversation preferences, captions, memory-only history and explicit tablet fallback.
- Portable dashboard template and installer include the shared modules; legacy house functions have grouped navigation. No APK, worker or backend update required.

## 0.3.1 — Developer Preview
- Contextual follow-ups in the same conversation, bounded time and supported read-only topics.
- Optional administrator-approved learning for generic unmatched home-data queries; no audio recording or general transcript log, bounded in-memory suggestions and local aliases.
- Dedicated admin Learning page, authenticated WebSocket API, German/English UI and tests.
- Valid ASCII selector translation IDs while retaining existing stored values and announcement API compatibility.
- Declare HA config-entry schema. Repository description/topics still required for HACS.

## 0.3.0 — Developer Preview
- Flexible local German intent recognition with normalization, synonyms and time-scope checks.
- Selectable source entities in integration Options and a standalone data-source status page: weather, Bring!/to-do, collection dates, heating, appliances and energy.
- Single-item shopping-list add/remove/check/read, exact names and post-operation verification.
- Waste collection queries offer confirmed reminders; one persistent item, HA notification and optional Echo playback.
- No household-specific entity mappings or automatic migration. Synthetic tests and DE/EN documentation; fresh HA installation pending.

## 0.2.2 — Developer Preview
- German and English project and installation documentation; translated Marketplace selectors and dashboard cards.
- Standalone sidebar voice center with native Assist launch, speech-service status, Bluetooth keepalive and announcements. No private dashboard or legacy helpers required.
- German speech grammar/models and legacy templates unchanged; fresh installation remains to be tested.

## 0.2.1 — Developer Preview
- Document DuckDNS IP updates through the Home Assistant app and separate Certbot certificates on the proxy.
- Explicit shared-proxy mode for a new hostname on existing Debian Nginx containers, without adopting existing sites.
- Check hostname conflicts, preserve default site and existing renewal schedule in shared mode.
- Hostname guard tests; existing production installations unchanged.

## 0.2.0 — Developer Preview
- Marketplace-style single integration with hacs.json, German/English configuration, STT/TTS and conversation routing, optional Alexa announcement action.
- Connection settings and sound profiles in the configuration dialog instead of source placeholders; optional Assist and Bluetooth cards.
- Dedicated unprivileged Nginx proxy with ACME/Certbot, restricted audio route, renewal and installation guide.
- Legacy installer and timer/notification templates retained; no automatic migration; end-to-end installation pending.

## 0.1.0 — Developer Preview
- Initial public project under Tablet Assist for Alexa.
- CPU speech server with Piper, Faster Whisper, MP3 sound profiles and cache; Proxmox/Debian installers.
- Sanitized HA integrations, conversation router, live profiles, reminders, configurable notifications and dashboard cards.
- Original GPU worker 1.5.0, Windows setup plus Linux setup, no private configuration.
- MIT license for original code; dependency/model licenses separate.
- Source checks and local audio tests; clean installation, GPU inference and device compatibility still need testing.
