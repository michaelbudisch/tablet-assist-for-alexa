# TAFA backend consolidation

[Deutsch](../backend-roadmap.md)

## Current installation
Marketplace installs only `custom_components/tablet_assist_for_alexa` (0.3.1). The separate backend under `homeassistant/custom_components/jarvis_tablet_audio` is not installed. Device Bridge 1.0.0 and CPU/GPU services are independent installations.

## Implementation and acceptance checklist
- Consolidate backend modules into the Marketplace domain; retain authenticated legacy HTTP paths and service/event compatibility where necessary. Do not copy two integration directories into the Marketplace root.
- Replace private hosts and entity mappings with config-flow options. Never publish tokens, household data, camera frames, private dashboards or backups.
- Integrate device registration, room audio, wake-word routing, optional camera/motion and vision, model configuration and announcements. Camera and microphone features require explicit permission.
- Provide a migration path for legacy entries, preserving identifiers and room assignments; prevent duplicate services and providers.
- Test setup, unload, reload, authorization, device pairing, multiroom isolation, CPU fallback and worker failure on a clean instance; verify APK 1.0.0 compatibility.
- Validate Marketplace install and upgrade from the repository link. Update DE/EN instructions and version/changelog only when a tested release is available.

The private TAFA dashboard is excluded. This checklist is not a release or a claim that the consolidation has already been implemented.
