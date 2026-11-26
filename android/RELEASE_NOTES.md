# TAFA Device Bridge 1.0.6

- Optional silent Bluetooth keepalive is directly visible on the Status/player card, including live state.
- Automatic recovery after Bluetooth interruptions, route changes, audio-focus loss or player errors, with a 3–30 second retry delay. System volume is unchanged and no separate audio focus is requested.
- Successful native audio connection enrolls the tablet in TAFA and keeps its online status current even without the wakeword service running.
- Native Assist processing, unlimited follow-ups, device management and the existing authenticated per-user Bluetooth audio connection are retained.
- Signed release APK **TAFA-Device-Bridge-1.0.5.apk**, version code **18**, with the existing de.jarvis.audio application ID and signing certificate. Install over the existing app to preserve credentials and device identity.

Keepalive remains optional per tablet and runs only while the player is active. It may reduce Echo idle announcements but cannot guarantee suppression. Compatible current TAFA/HA components are required. Physical Bluetooth, microphone and multi-device testing on real tablets remains outstanding.
