# TAFA — Tests and release checklist

**English** | [Deutsch](../release.md) · [Project overview](../../README.md)

**Current state:** TAFA Home Assistant App **0.3.10** (experimental release candidate), unified HA integration **0.4.3**, Android Device Bridge **1.0.0 unchanged**. No production or hardware certification.

## Automated checks

GitHub Actions workflows provide:

- `python scripts/test_unified_layout.py`: one integration, app/Marketplace bundle matching, no placeholders/private network addresses, native compatibility API
- `python -m unittest discover -s tafa_app/tests -v`: safe installation and rollback, Ingress/CSRF, Piper/Whisper HTTP API, and mocked HA config/Assist pipeline
- `node --input-type=module --check < custom_components/tablet_assist_for_alexa/frontend/panel.js`: public UI syntax
- `python tests/test_marketplace.py` and HACS/hassfest: integration structure and dependencies
- `bash tests/ha_e2e/run.sh`: actual Home Assistant Core Docker startup, native relay services, multiroom, camera/motion entities, conversation, restart and persisted reminders
- `linux/amd64` and `linux/arm64` Docker image builds in `.github/workflows/tafa-app.yml`.

Previous successful CI runs validate **source, image build and HA Core behavior**, not an entire fresh Home Assistant OS/Supervisor installation with real downloaded CPU models or physical tablets. Verify current HEAD checks independently after changes.

## Outstanding stable-release gates

1. Full clean Home Assistant OS installation including App Store, Supervisor APIs, Ingress and automatic pipeline.
2. Real Piper/Whisper model download, RAM/CPU use, and speech quality on amd64/aarch64.
3. Echo Bluetooth playback and simultaneous physical Android multiroom tests.
4. **Native wake handoff:** unchanged Device Bridge 1.0.0 sends only the matched wake phrase and releases its microphone. It does not stream the subsequent spoken question. A separate active Assist client must capture speech. Fully hands-free use with just this Bridge and the TAFA App is **not yet supported**.
5. Legacy migration with existing `jarvis_tablet_audio` entries and room assignments must be tested on backed-up copies.
6. Security/voice-model license reviews and final stable tag only after these checks.

**Release policy:** Keep App config version, integration manifest, `VERSION`, both changelogs and DE/EN guides consistent. Exclude private dashboards, household secrets, tokens, and changes to the Android APK.

[App setup](app.md) · [Marketplace](marketplace.md) · [Backend](backend-roadmap.md) · [GitHub Actions](https://github.com/michaelbudisch/tablet-assist-for-alexa/actions).
