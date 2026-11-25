# HA Jarvis Echo Relay 0.9.0 · Dynamic multiroom (test build)

Unlimited Android Wake Pilot installations can now register with a persistent random device ID and a friendly room name. Home Assistant maintains independent settings for every enrolled device without manually creating helpers or reserving fixed slots.

In TAFA → Jarvis → Voice & Audio, refresh the registered-device list, select and pair the desired tablet with the dashboard, then edit its mute state, wakeword, sensitivity confirmations, cooldown and microphone handoff. The central HA API selects the first arriving simultaneous wakeword within a three-second window; this is not acoustic localization.

**Experimental test branch:** Validate on real Android devices. Existing Echo Relay audio routing is unaffected, and the separate debug APK is named **HA Jarvis Echo Relay (Test)** and does not replace the signed, regularly released app.
