# TAFA Home Dashboard · Changelog

## 0.2.1 — Release Candidate (2026-11-24)

- Coalesce Home Assistant state updates over a 250 ms window.
- Cancel pending refreshes safely on card disconnection.
- Add three regression checks for batched state updates and cleanup; 38 synthetic tests total.
- Stage optional rendering/FPS, voice-timing and Echo Relay diagnostic modules.
- Do not publish private household configuration.

**Status:** Release candidate on a separate branch. Hardware-level tablet, microphone, Bluetooth and clean-install validation remain. This portable preview does not fully replace the private kiosk dashboard.
