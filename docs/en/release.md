# TAFA – tests and release checklist

[Deutsch](../release.md) · [Project](../../README.md) · [Setup](setup-guide.md)

**Authoritative versions:** The **TAFA App** version lives in [`tafa_app/config.yaml`](../../tafa_app/config.yaml), the **HA integration** in its [`manifest.json`](../../custom_components/tablet_assist_for_alexa/manifest.json), **Device Bridge** in [`android/VERSION`](../../android/VERSION), and the **GPU worker** in [`worker/VERSION`](../../worker/VERSION). A signed Android APK release may differ from current source.

## Automated validation

GitHub Actions workflows check, as applicable, Python/JavaScript/Shell syntax, HA integration and Proxmox installer tests, App install/rollback behavior, GPU worker scripts, Android build and configuration contracts. Public documentation is additionally checked using **`python tests/test_docs_public.py`** (relative links, personal setup defaults, key onboarding contracts) and **`python tests/check_sources.py`**.

**Green CI is not a complete fresh-install test on physical hardware.** Verify the actual workflows for the release commit and rerun relevant tests whenever installation scripts change.

## Manual clean-install checklist

1. On a clean **HA OS 2026.11+** machine, back up HA and install TAFA from the App repository. Initial state must be `speech_mode=setup` with **no bundled model download until mode selection**.
2. **Local:** start Piper/Faster-Whisper after selecting `local` and test speech. **External:** configure a Proxmox CPU server, Piper HTTP and a separate CPU Wyoming `stt.*` entity.
3. **HA integration/pipeline:** After HA Core restart, verify the three **TAFA Lokal** routers and preservation of existing pipelines and automations.
4. **Android:** Install the current **signed** Device Bridge, connect a non-admin room user, test wakeword/microphone and actual Bluetooth Echo media playback.
5. **Optional GPU:** Verify Windows/Linux worker, import GPU JSON under **Connections**, add Wyoming and Ollama **in HA**, and test GPU online/offline CPU Whisper/Piper fallback. A CPU text-LLM fallback is not automatic.
6. **Multiroom:** Pair at least two physical tablets/rooms and verify simultaneous requests and routing. Test camera/Vision only after explicit opt-in.
7. **Optional Alexa MP3:** Verify remote HTTPS file retrieval while keeping internal generator ports closed. Ordinary Bluetooth replies must be independent of public audio hosting.
8. **Upgrade/migration:** Distinguish App-managed integrations from Marketplace/legacy Jarvis; check backup, rollback and retained data on a separate test install.

**Release claim:** Do not label a build “fully tested” or “certified” without documented live hardware/network checks. Record any known limitations and exact tested combinations per release.
