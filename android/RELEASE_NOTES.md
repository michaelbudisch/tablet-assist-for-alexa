# HA Jarvis Echo Relay 0.7.1

Signed release APK: **HA-Jarvis-Echo-Relay-0.7.1.apk**. Install over the existing signed app to preserve the address, token and preferences. Application ID `de.jarvis.audio` and the existing signing certificate are retained. The version code increases to **10**. The APK is a non-debuggable release build.

## Changes

- Remote native microphone mute via `input_boolean.jarvis_native_wake_stumm`; muting releases the Android microphone.
- Wakeword, recognition strictness (1–3 confirmations), cooldown (3–30 seconds) and microphone handoff pause (10–90 seconds) are configurable in the app and synchronized with Home Assistant.
- Rearming uses the configured handoff pause. HA mute is checked about every 2.5 seconds and full settings about every 12 seconds. If HA settings are unavailable, the microphone is released.
- Optional offline German Vosk recognition: Hey Jarvis, Jarvis, Alexa or all three. Detection is off by default; microphone access and the approximately 45 MB model download require explicit user action. No automatic startup after reboot.

## Setup and limits

The [Android setup guide](README.md#native-microphone-and-wakeword-settings-071) lists the five required Home Assistant helpers. Configure them and a dashboard listener for `jarvis_android_wakeword` separately; the APK does not install HA helpers or dashboard code. Without the helpers, native recognition remains muted. Keep the compatible dashboard open for Whisper STT and disable its competing wakeword detector. Only recognized wakeword text is sent to HA; wakeword audio stays local.

The existing Bluetooth audio player and camera remain available. Wakeword recognition quality, background operation, audio handoff and microphone coexistence still require physical-device testing. Words immediately following the wakeword may be lost during handoff. Selecting Alexa may also trigger a physical Echo.

## Validation

Built from Android source `efaa578af697d4580890405f1f51531302fde383` with Java 17. Release assembly, JVM tests, Android lint and instrumentation-test compilation passed. APK signature, package/version metadata and 16 KB ZIP alignment were verified. A previously validated HA fixture correction is included so the current settings schema is used. No physical-device test was performed.
