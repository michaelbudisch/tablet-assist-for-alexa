# Legacy Echo Relay Lovelace cards (migration only)

[Deutsch](../echo-relay-dashboard.md) · [Current TAFA setup](setup-guide.md) · [Current Multiroom](../../homeassistant/examples/MULTIROOM.md)

**Not for new TAFA installs:** The old separate Jarvis/Echo Relay cards, manual `input_text` helpers, `jarvis_tablet_audio` services and JavaScript resources are not needed with the unified TAFA integration.

Current path: Connect the signed [TAFA Device Bridge](../../android/README.md) to Home Assistant, verify the **TAFA Lokal** pipeline, and manage tablets under **TAFA → Devices & Multiroom**. Ordinary voice replies play on Android/Bluetooth. **TAFA → Speak now** is a separate browser test.

If you are migrating an existing Jarvis dashboard, the [archived reference](../archive/legacy-echo-relay-dashboard.en.md) is kept for context. Back up HA and audit existing automations before migrating.
