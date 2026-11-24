# Jarvis multiroom — development proposal

**Not integrated or production-ready.** Keep the existing central GPU worker and CPU fallback. Phase one is an isolated, tested-in-CI audio routing registry for explicitly assigned rooms. No private dashboard modules, live configuration, or camera images are included.

An administrator provisions each Relay device. Device IDs are not credentials; the future HA adapter must enforce authenticated principals, device-bound sessions, revocation and migration. The Relay app receives only its own audio jobs; its Echo remains locally paired. Replies must never silently fall back to a different room. A fresh heartbeat and idle status are required; jobs are short-lived and single-claim, with playback acknowledgement in the future adapter. Route conversation context per device. Optional occupancy can use local motion sensors; no cross-room identity tracking. Camera and microphone permissions must be separately visible and controllable, with cameras off by default in private rooms and no persistent indoor imagery.

Phases: isolated routing/tests; HA registration/authenticated audio bridge; Android client; two-device tests (busy, offline, restart, parallel requests); portable dashboard management. The existing single-device flow remains untouched until the new path is validated.
