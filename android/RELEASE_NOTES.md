# HA Jarvis Echo Relay 0.6.0

Room-specific audio, camera JPEG feeds and optional local motion detection. Each shared room uses a dedicated non-admin Home Assistant account and explicit camera permission; camera transmission starts only on the tablet and has a separate visible stop control. Choose a 1, 2, 3, 5 or 10 second refresh interval. Version and build number appear on the home screen. Existing single-device mode remains available. Requires matching HA 1.7.0 for room cameras.

Release APK must be signed with the existing application signing key to update the installed 0.5.0. CI can build unsigned release output without secrets; that output cannot be installed. No new signing identity is generated. Hardware validation on two tablets remains required.
