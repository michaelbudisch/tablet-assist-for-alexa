**English** | [Deutsch](CHANGELOG.de.md)

# Changelog

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
