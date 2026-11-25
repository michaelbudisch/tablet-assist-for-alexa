# HA Jarvis Echo Relay 0.7.1 · experimental

This branch adds opt-in German Vosk wakeword detection with four selectable modes: Hey Jarvis, Jarvis, Alexa or all three. The app requests microphone permission only when starting the detector, installs the ~45 MB offline model only on explicit user action, and forwards recognized wakewords (no audio) to Home Assistant. A matching dashboard listener launches the existing STT pipeline. A foreground notification provides a Stop control.

**Test branch, not a published signed APK.** Model loading, recognition quality, background operation, audio handoff and device compatibility still require real Android testing. The already published 0.6.0 update remains the stable downloadable APK.

0.7.1 also adds app/HA controls for microphone mute, phrase selection, recognition confirmation count, cooldown and handoff time. Mute releases the microphone and an HA outage fails closed. A calibrated dB trigger threshold is not available.
