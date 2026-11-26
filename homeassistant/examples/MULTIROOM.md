# TAFA Multiroom – multiple tablets

[Deutsch](MULTIROOM.de.md) · [Project](../../README.md) · [Setup](../../docs/en/setup-guide.md)

**Current fresh-install path:** Multiroom is part of the unified TAFA integration and **TAFA Device Bridge 1.2.1**. Old separate Jarvis integrations, helpers, Lovelace cards and Android 0.x APKs are **not required**. The [historical Multiroom guide](archive/legacy-MULTIROOM.md) is kept for migration only.

## Requirements

- [TAFA App and TAFA Lokal](../../docs/en/setup-guide.md) with CPU Piper/Whisper running locally in TAFA or on an external speech server.
- The signed [TAFA Device Bridge](../../android/README.md) installed on each Android 9+ tablet; microphone and audio permissions granted.
- One **dedicated active non-admin HA user per tablet/room**. Do not share one access token across multiple rooms.
- Optional Echo paired as an **Android Bluetooth media speaker** on each tablet; normal Alexa use remains possible.

## Pair a room and device

1. Create a **separate non-admin HA account** for each tablet.
2. Under **TAFA → Devices & Multiroom**, create/select a room and assign that account. Rooms can be created before tablets enroll; there is **no four-device cap**.
3. In Device Bridge **Connect**, provide the correct HA base URL (without dashboard path) and **that room user's token**. Start the local wake service to enroll the device.
4. In **TAFA → Devices & Multiroom**, select the enrolled tablet, assign the room/user and choose **Connect audio room**. Explicit confirmation is required for a transfer from another user.
5. On Android enable **Multiroom audio** and **Start player**. Check **connected**, **player ready** and **last seen** in TAFA.
6. Ask a short question on **that tablet**. For Echo playback, pair the Echo as the tablet's Bluetooth media output.

A registered wake device does **not** by itself prove audio room pairing. If playback shows offline, check the native player/network; if not ready, check Android media output. The Assist pipeline must use **Tablet Assist Stream** TTS. Control Center's browser **Speak now** test plays **in the browser** and does not automatically confirm room/Echo playback.

## Optional camera and device settings

Explicitly grant **tablet camera permission per room** in **Devices & Multiroom** (default **off**), then start the camera on the tablet. The assigned non-admin room user works; no administrator camera token is needed. Recent JPEG stills and coarse image motion are not continuous video or identity detection. See [camera setup](../../android/docs/camera-preparation.md).

Microphone modes and device information can be controlled from TAFA/Device Bridge. Inform others sharing the room about active camera or microphone features. A non-admin HA account is **not** a general isolation boundary for every HA entity.

## Troubleshooting and legacy

- **Device missing:** Check Device Bridge connection, assigned HA user and running wakeword service.
- **No Echo speech:** Check Android Bluetooth media output, native player and **Tablet Assist Stream**.
- **Speech slow/offline:** Check CPU/GPU Wyoming under **TAFA → Connections**; CPU fallback is independent of Multiroom.
- **Old Jarvis cards or automations:** Do not deploy them alongside a fresh TAFA install. Back up HA and review migration manually before removing legacy components.

**Security:** Do not publish HA tokens in YAML/Git/screenshots. Plain local HTTP transmits credentials without encryption; prefer trusted HTTPS. Granting a camera permission does not automatically start capture.
