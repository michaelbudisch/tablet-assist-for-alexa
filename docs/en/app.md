# Install TAFA from Home Assistant Apps

## Current interface · TAFA App 0.3.43 / integration 0.4.25

The **TAFA Control Center** uses five areas:

1. **Overview:** voice route and component status, without configuration fields.
2. **Connections:** Three groups: **GPU/AI preferred route** (direct GPU PC IP, Qwen TTS, GPU Wyoming STT dropdown and optional Ollama `conversation.*` entity); **CPU fallback** (Piper and CPU Wyoming STT); **Alexa** (MP3 generator and public HTTPS). Live address checks run while typing; choose JSON file → check → confirm changes remains here.
3. **Settings:** Local/external mode, GPU/Piper speech routing, voices, conversation behavior, optional Alexa announcements and HA sources. **No IP/domain or Wyoming entity fields.**
4. **Devices & multiroom:** enroll, pair, **unpair**, **remove tablet** or **delete room**. Only TAFA assignments and TAFA-owned entities are cleared. HA users and automations remain, although automations referencing removed entities may need to be reconfigured.
5. **Maintenance & help:** backend status, model files, restart and documentation.

**Fast GPU check:** Enter the private GPU PC IP (e.g. `192.168.178.115`) into **GPU PC IP – fast probe (Wyoming port 10300)**. The TAFA STT router checks TCP port 10300 with a **0.8 s timeout** before GPU recognition; when offline it uses the CPU Wyoming fallback. The selected GPU Wyoming entity performs the actual transcription. Qwen TTS independently checks its `/health` endpoint and uses Piper when unavailable. A listening port is not proof of successful STT. CPU and GPU Wyoming entities must differ.

**Verification limit:** HTTP/TCP connectivity does not prove live speech. Public Alexa HTTPS checks DNS and TLS validity, not actual audio-file retrieval from Amazon. Edits are only saved when you select Save.

To keep a tablet removed, first stop its player and wakeword services; an active Device Bridge can enroll again. Restart HA Core once after updating the backend.

---

## Older setup notes (historical releases)


[Deutsch](../app.md) · [Project overview](../../README.md)

> **From App 0.3.20:** Use **TAFA Control Center → Settings** to configure all TAFA features. The technical **Apps → TAFA → Configuration** is an advanced view of the same persistent options, especially useful before the first start to choose external speech without downloading local models. Restart TAFA after saving. Wyoming/Ollama are added once in Devices & services; existing Assist pipelines are preserved.


**TAFA App 0.3.12 — release candidate, not yet certified on a clean HA OS device.** Requirements: Home Assistant OS 2026.11+ and a supported amd64/aarch64 machine; enough memory and disk space for German CPU speech models. Android Device Bridge 1.0.0 is unchanged.

**New:** [Guided setup for TAFA local, Proxmox, GPU worker and Alexa MP3](setup-guide.md). All TAFA options are managed together in **Control Center → Settings**.

## Primary App setup and live connection checks

Start in **TAFA Control Center → Settings**: choose local/Proxmox Piper, optional GPU-Qwen URL, automatic Qwen-to-Piper fallback, voice variant, sound profile, and optional Alexa MP3/HTTPS URLs. DE/EN field descriptions are provided. Restart TAFA after saving. New HA integration entries inherit these settings. Existing App-managed entries are synchronized from App Configuration after restart.

The **Control Center → Connection diagnostics** refresh link checks GPU readiness/busy/offline, Piper fallback and MP3 generator health without generating speech or announcements. The expected route is based on App options, not necessarily on an older HA integration configuration.

The **Control Center → Manage local speech models** section shows TAFA-owned download sizes. To remove them, select **external** speech mode, restart TAFA, and type **ENTFERNEN** to confirm. Proxmox, Wyoming and other HA apps are untouched.

## One-App setup

1. Create a Home Assistant backup. Prefer a clean test instance for the first deployment.
2. Open **Settings → Apps → Install app → Repositories**, add `https://github.com/michaelbudisch/tablet-assist-for-alexa` and install **TAFA**. **Before starting**, use the App **Configuration** tab to select `speech_mode=local` or `speech_mode=external` with `external_piper_base=http://PROXMOX-IP:5000`.
3. Start the App and open **TAFA Control Center**. Only local mode downloads CPU voice models. External mode skips bundled model startup and checks the Proxmox Piper connection.
4. TAFA stages **one** component: `custom_components/tablet_assist_for_alexa`. Restart Home Assistant **once** using the normal Home Assistant settings. No YAML edits or second HA integration are needed on a fresh installation.
5. The App attempts to configure the TAFA integration. Local mode then attempts to create **TAFA Lokal**. In external mode add the Proxmox **Wyoming** integration at `PROXMOX-IP:10300`, select its STT entity as CPU STT under **Apps → TAFA → Configuration**, and manually create an Assist pipeline using the TAFA STT router and **Tablet Assist Stream**. Existing pipelines are unchanged; never edit `.storage`.
6. Install/connect the existing [TAFA Device Bridge 1.0.0](../../android/README.md); select the TAFA Lokal pipeline in Home Assistant Assist (or the HA Companion app), not in Device Bridge. Optionally pair an Echo as the Android Bluetooth output. The app's audio, camera and wake-word permissions remain under Android user control.

## Native wake-word limitation

Device Bridge 1.0.0 sends the recognized wake word and releases its microphone but does not transmit the following question. An active Assist client must capture the question after that event; no backend-only change can recover missing audio. Direct manual Assist works. Do not advertise fully hands-free operation with only the unchanged Bridge until the handoff is independently tested and supported.

## Automatic Qwen/Piper speech output

Starting with TAFA App 0.3.12, a **newly created** `TAFA Lokal` Assist pipeline selects the **Tablet Assist Stream** TTS provider by default. Without a configured or reachable GPU worker it uses Piper. Once the Qwen worker URL is explicitly configured in the **TAFA integration under Settings → Devices & services**, the router prefers Qwen when healthy and falls back to Piper if unavailable. TAFA does not scan for GPU hosts.

**Existing TAFA Lokal pipelines are not changed automatically.** For an existing Piper-only pipeline, select **Tablet Assist Stream** as the TTS engine in the Assist pipeline settings. The Qwen/Piper router applies to native Assist speech output; Alexa MP3 announcements via the HTTPS proxy are separate.

## What is bundled

- One HA integration provides STT, TTS, conversation, native wake-device registry, authenticated compatibility API, multiroom audio, optional cameras/motion and vision services.
- **Local mode:** Piper and Faster-Whisper run in the App, with models in `/data`. **External mode:** bundled CPU model startup/downloads are skipped and Proxmox Piper/Wyoming remain separate. No public app port is mapped.
- The GPU worker, Ollama and Alexa MP3/HTTPS notifications remain optional and must be configured separately.
- This App does not install the private TAFA dashboard or modify Android/APK source.

## Troubleshooting: Docker build fails on a virtual CPU

If Supervisor reports `NumPy was built with baseline optimizations: (X86_V2) but your machine doesn't support (X86_V2)`, a generic virtual CPU profile may lack the required instruction set. **App 0.3.9 pins NumPy 1.26.4**, avoiding the x86-64-v2 baseline introduced in NumPy 2.4. Refresh the App repository, install **TAFA 0.3.12**, and keep your existing HA integration and App data. Other native libraries may have independent CPU feature requirements; investigate separately if an `illegal instruction` persists.

## Troubleshooting: Piper or Whisper not ready

The initial App 0.3.4 test could terminate Piper with `RuntimeError` and Whisper with `ImportError`. From 0.3.9 the container validates native speech-library imports during its build, includes eSpeak runtime/data, and shows the underlying initialization error (not only the exception class) in Control Center.

Update the TAFA App under **Settings → Apps → TAFA**, restart the App, and inspect both model statuses in Control Center. Initial model downloads require internet and can take time. Use **Retry speech models** when a model reports an error. If it persists, inspect the detailed Control Center error and TAFA App log. No HA integration reinstall is needed for these speech dependencies.

## Updates, safety and limitations

- The App automatically stages the integration and updates it **only if TAFA originally installed it and its files are unchanged**. Before a managed update it saves the prior version under `<HA config>/.tafa/rollback`. HACS/manual installations and edited files are never overwritten. Restart HA after backend updates.
- An older configured `jarvis_tablet_audio` can conflict with duplicate native endpoints. TAFA detects it and skips duplicate registration; it does not delete, overwrite or automatically migrate the old integration. Backup and migrate separately.
- Microphones/cameras are opt-in. Audio/STT requests are processed in memory; the built-in speech API limits request sizes. Initial model downloads need internet; there is no guaranteed offline first install.
- Known release gate: clean HA OS install, model download, end-to-end Assist/Device Bridge/Bluetooth and simultaneous physical Multiroom tests still need confirmation. See [release checklist](release.md).

[Marketplace-only instructions](marketplace.md) · [Multiroom](../../homeassistant/examples/MULTIROOM.md) · [Optional GPU worker](worker.md)
