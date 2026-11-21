# Tests und Release-Checkliste

Öffentliche Entwicklungsvorschau 0.1.0 (keine stabile produktionsfertige Version).

```bash
python3 tests/check_sources.py
python3 tests/test_audio.py
```

Die Audio-Tests verwenden synthetische Signale und einen Stub für Flask, laden kein TTS-Modell. Sie prüfen nicht die echte HA-/GPU-/Alexa-Kompatibilität.

Vor einem stabilen Release: frische Debian-CT-/HA-Installation, STT und GPU-Inferenz, CPU-Fallback bei abgeschaltetem Worker, Tablet-Echo-Bluetooth-Pairing, Durchsagen, Ruhezeiten, Gerätezuordnung, Neustart und Sicherheitsprüfung. Keine privaten Konfigurationen oder Modelldateien committen. VERSION und CHANGELOG bei Releases gemeinsam aktualisieren; die separat versionierte Original-Worker-Komponente bleibt bei 1.5.0.
