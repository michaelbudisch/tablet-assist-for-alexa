# Unified TAFA Backend 0.4.2 — release candidate

[Deutsch](../backend-roadmap.md)

## Implementation

The public backend previously under `homeassistant/custom_components/jarvis_tablet_audio` has been merged into the single `custom_components/tablet_assist_for_alexa` domain. The compatibility subpackage `relay/` retains existing authenticated Device Bridge REST endpoints and room events. Only one custom integration is installed on fresh HA systems; CPU Piper and Faster-Whisper are provided by the separate TAFA **Home Assistant App process**, not by the Marketplace integration. The private TAFA dashboard is not shipped.

The first-run App copies an integrity-checked public component, starts the internal CPU speech API and uses Home Assistant config flow/API calls to configure the TAFA integration and a separate `TAFA Lokal` Assist pipeline. App-managed upgrades preserve backups. Android Device Bridge 1.0.0 is unchanged.

## Release acceptance and known gaps

- Implemented: single-domain public backend, native compatibility endpoints, multiroom/camera relay modules, Piper/Whisper CPU app, bilingual Ingress Control Center, source-level and Docker CI.
- Automated: HA runtime, HACS/hassfest, component bundle checks, speech API unit tests and installer rollback tests.
- Not yet verified on real hardware: clean HA OS install, runtime CPU model downloads, full voice roundtrip on Device Bridge, Bluetooth Echo playback, simultaneous multiroom tablets.
- Existing `jarvis_tablet_audio` config entry/storage/pipelines are not migrated automatically. On existing installs, the new integration disables its duplicate native relay registration while an old entry exists. Back up and migrate legacy environments separately.
- Do not tag stable until an end-to-end HA OS test and Android-device compatibility test pass. Additional private or household features are out of scope.

[App installation](app.md) · [Marketplace](marketplace.md) · [Release checklist](release.md).
