# Tests and release checklist

**English** | [Deutsch](../release.md) · [Project overview](../../README.md)

Public developer preview 0.3.1 (not a production-ready stable release).

```bash
python3 tests/check_sources.py
python3 tests/test_audio.py
python3 tests/test_install.py
python3 tests/test_marketplace.py
python3 tests/test_proxy.py
python3 tests/test_proxy_host.py
```

Audio tests use synthetic signals and a Flask stub, without loading a TTS model. These are not tests of real HA, GPU or Alexa compatibility.

Before a stable release: fresh Debian CT and HA installation, STT and GPU inference, CPU fallback with the worker offline, tablet/Echo Bluetooth pairing, announcements, quiet times, device mapping, restart and security review. Never commit private configuration or models. Update VERSION and both changelogs together. The separately versioned original GPU worker remains at 1.5.0.

Public catalog inclusion requires additional validation, a release tag and successful CI. Test Add from link on HA 2026.11. Installers, GPU and HTTPS playback must be checked on real equipment.

Additional tests: `python3 tests/test_local_intents.py` (synthetic states, no live HA install).
