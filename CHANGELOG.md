## Integration 0.4.0 — unified backend candidate
- Single TAFA integration with native Device Bridge API compatibility, multiroom services, camera/motion and opt-in vision. CPU STT can use the local TAFA App. The existing Android APK is unchanged.
- Release acceptance: automated checks plus clean HA OS installation and real-audio testing required before marking stable.

# Changelog

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
