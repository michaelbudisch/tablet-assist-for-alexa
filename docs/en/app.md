# Install TAFA from Home Assistant Apps

[Deutsch](../app.md) · [Project overview](../../README.md)

**TAFA App 0.3.6 — release candidate, not yet certified on a clean HA OS device.** Requirements: Home Assistant OS 2026.11+ and a supported amd64/aarch64 machine; enough memory and disk space for German CPU speech models. Android Device Bridge 1.0.0 is unchanged.

## One-App setup

1. Create a Home Assistant backup. Prefer a clean test instance for the first deployment.
2. Open **Settings → Apps → Install app → Repositories**, add `https://github.com/michaelbudisch/tablet-assist-for-alexa`, select **TAFA**, install and start.
3. Open the **TAFA Control Center**. CPU models download on first launch (network access needed). The status tiles distinguish real Piper/Whisper readiness from pending or failed initialization.
4. TAFA stages **one** component: `custom_components/tablet_assist_for_alexa`. Restart Home Assistant **once** using the normal Home Assistant settings. No YAML edits or second HA integration are needed on a fresh installation.
5. The App attempts the HA integration config flow through the Supervisor Core API and then creates a **TAFA Lokal** Assist pipeline when STT, TTS and the conversation router are registered. Existing HA pipelines remain untouched. If automatic setup is unavailable, open **Settings → Devices & services → Add integration → TAFA**, then select the built-in Piper service and HA Assist pipeline from Control Center. Do not manually edit `.storage`.
6. Install/connect the existing [TAFA Device Bridge 1.0.0](../../android/README.md); select the TAFA Lokal pipeline in Home Assistant Assist (or the HA Companion app), not in Device Bridge. Optionally pair an Echo as the Android Bluetooth output. The app's audio, camera and wake-word permissions remain under Android user control.

## Native wake-word limitation

Device Bridge 1.0.0 sends the recognized wake word and releases its microphone but does not transmit the following question. An active Assist client must capture the question after that event; no backend-only change can recover missing audio. Direct manual Assist works. Do not advertise fully hands-free operation with only the unchanged Bridge until the handoff is independently tested and supported.

## What is bundled

- One HA integration provides STT, TTS, conversation, native wake-device registry, authenticated compatibility API, multiroom audio, optional cameras/motion and vision services.
- The App contains **local German Piper and Faster-Whisper CPU engines**. Their downloaded models persist in the HA App's `/data` volume. They listen on the internal app network; no public port is mapped.
- The GPU worker, Ollama and Alexa MP3/HTTPS notifications remain optional and must be configured separately.
- This App does not install the private TAFA dashboard or modify Android/APK source.

## Troubleshooting: Docker build fails on a virtual CPU

If Supervisor reports `NumPy was built with baseline optimizations: (X86_V2) but your machine doesn't support (X86_V2)`, a generic virtual CPU profile may lack the required instruction set. **App 0.3.6 pins NumPy 1.26.4**, avoiding the x86-64-v2 baseline introduced in NumPy 2.4. Refresh the App repository, install **TAFA 0.3.6**, and keep your existing HA integration and App data. Other native libraries may have independent CPU feature requirements; investigate separately if an `illegal instruction` persists.

## Troubleshooting: Piper or Whisper not ready

The initial App 0.3.4 test could terminate Piper with `RuntimeError` and Whisper with `ImportError`. From 0.3.6 the container validates native speech-library imports during its build, includes eSpeak runtime/data, and shows the underlying initialization error (not only the exception class) in Control Center.

Update the TAFA App under **Settings → Apps → TAFA**, restart the App, and inspect both model statuses in Control Center. Initial model downloads require internet and can take time. Use **Retry speech models** when a model reports an error. If it persists, inspect the detailed Control Center error and TAFA App log. No HA integration reinstall is needed for these speech dependencies.

## Updates, safety and limitations

- The App automatically stages the integration and updates it **only if TAFA originally installed it and its files are unchanged**. Before a managed update it saves the prior version under `<HA config>/.tafa/rollback`. HACS/manual installations and edited files are never overwritten. Restart HA after backend updates.
- An older configured `jarvis_tablet_audio` can conflict with duplicate native endpoints. TAFA detects it and skips duplicate registration; it does not delete, overwrite or automatically migrate the old integration. Backup and migrate separately.
- Microphones/cameras are opt-in. Audio/STT requests are processed in memory; the built-in speech API limits request sizes. Initial model downloads need internet; there is no guaranteed offline first install.
- Known release gate: clean HA OS install, model download, end-to-end Assist/Device Bridge/Bluetooth and simultaneous physical Multiroom tests still need confirmation. See [release checklist](release.md).

[Marketplace-only instructions](marketplace.md) · [Multiroom](../../homeassistant/examples/MULTIROOM.md) · [Optional GPU worker](worker.md)
