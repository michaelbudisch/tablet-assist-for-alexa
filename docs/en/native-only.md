# TAFA – native voice path and central management

[Deutsch](../native-only.md) · [Setup](setup-guide.md) · [Android](../../android/README.md)

## Voice route

**TAFA Device Bridge (Android)** detects the wake word and records the question → **Home Assistant Assist / TAFA Lokal** → **Whisper (GPU or CPU)** → HA intents or optional Ollama → **Qwen or Piper** → **Android media player** → optional Bluetooth Echo.

For ordinary conversations, Echo is a Bluetooth **speaker**, **not** the microphone. No public audio domain is required for this route. Optional Alexa MP3 announcements use a separate HTTPS path.

## Setup and modes

1. Install the [TAFA HA App](app.md) and choose **Local** or **External** CPU speech mode. Fresh installs start in `setup`, with no automatic CPU model download.
2. Set IPs, Wyoming `stt.*` entities, and optional Ollama `conversation.*` under **TAFA → Connections**. The GPU JSON import is also there. Wyoming/Ollama entities must first be created in HA.
3. Verify the three routers in the **TAFA Lokal** pipeline. Install the [signed Device Bridge](../../android/README.md) and use a separate non-admin HA user for each tablet.
4. Optionally pair Echo via Bluetooth, start native playback, select a wake word, grant microphone permission.
5. Register tablets under **TAFA → Devices & Multiroom** and assign rooms. There is **no fixed four-room limit**.

Native Android microphone modes are **Muted**, **Wake word** and optional **Always on**. Device Bridge supports a **limited** number of follow-up questions; unlimited follow-ups are **not the default**. Always on may mistake background speech for a request. **TAFA → Speak now** is a **separate browser test** with transcript, timing and browser playback, not a replacement for native wake detection or an automatic Echo output test.

## Camera, display and limitations

Explicitly enable the **tablet camera** per room in **Devices & Multiroom** (default off), then start it in Device Bridge. Uploads are authenticated; a normal non-admin room user does **not** need an administrator token. Image/motion reporting uses fresh stills and is fallible. [Camera setup](../../android/docs/camera-preparation.md).

Optional Android display permissions support brightness adjustments; without privileged device management the app cannot reliably power the display fully on/off, wake from deep sleep or unlock it. Check the native microphone indication and device permissions after disconnection.

Existing HA dashboards, automations and other Assist pipelines are not silently modified. Signed APK updates require the **same certificate**; a CI debug APK cannot replace a signed release in place.
