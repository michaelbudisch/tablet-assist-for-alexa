**English** | [Deutsch](CHANGELOG.de.md)

# Changelog

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
