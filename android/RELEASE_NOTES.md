# TAFA Device Bridge 1.0.4

- Successful native Bluetooth playback connection now triggers background tablet enrollment in HA, even without the wakeword service. This makes the tablet appear in Devices & multiroom for remote controls and pairing.
- Native voice processing through Home Assistant Assist and the existing Bluetooth audio transport; no open browser dashboard required.
- Follow-up questions continue until silence, mute or stop instead of the previous two-question limit.
- HA-managed per-device speech pause and digital microphone gain, plus tablet, battery and Bluetooth telemetry.
- Optional display brightness adjustment after explicit Android special access. This does not physically power the screen off.
- Android version **1.0.4**, version code **17**, unchanged application ID `de.jarvis.audio`. An in-place update needs an APK signed with the original signing certificate; CI debug builds are not compatible signed updates.

Compatible current TAFA/HA components and a complete Assist pipeline with STT/TTS are required. Physical microphone, Bluetooth and multi-device testing on real tablets remains outstanding.
