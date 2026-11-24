# Jarvis multiroom — experimental 0.1

[Deutsch](MULTIROOM.de.md)

Use the existing central Home Assistant, GPU worker and CPU fallback. No additional worker is needed. The existing single-device mode stays available. This is a development build, not a published APK or a production-tested release.

## Setup on a test installation

1. Back up the current integration; install the complete integration directory from this branch (not the older Ring overlay), then restart HA.
2. Create a dedicated active non-admin HA account per room. Use that same account in its Relay app and room dashboard. Do not share room accounts or use admin tokens in Relay. Prefer your trusted HA HTTPS connection. Routing does not replace HA's general resource permissions.
3. Copy `jarvis-room-admin-v0.1.0.js` and `jarvis-room-assist-v0.1.0.js` from `homeassistant/www/jarvis/` to `/config/www/jarvis/`. Register both `/local/jarvis/...` URLs as dashboard JavaScript module resources.
4. Add `type: custom:jarvis-room-admin` to an administrator dashboard. Assign each room a dedicated HA user, optional HA device registry ID (with the appropriate area), and optional quiet hours. Leave both quiet times empty to disable quiet hours. The card also supports explicit multiroom announcements and revocation.
5. Install the Android CI test build. Configure the room account's HA token in the app, enable **Room audio (experimental)** and start the player. Pair each Echo locally via Bluetooth.
6. In each room's dashboard, signed in as that room's account, configure:
   ```yaml
   type: custom:jarvis-room-assist-card
   pipeline_id: YOUR_ASSIST_PIPELINE_ID
   instance_id: living_room
   ```
   Use a unique instance ID per room. Existing Assist and streaming TTS are reused. The card passes the assigned HA device ID into Assist for area context; room-relative commands require the correct device/area assignment and compatible HA agent.

## Announcements

```yaml
action: jarvis_tablet_audio.room_audio
data:
  action: announce
  rooms: [living_room, office]
  message: "Dinner is ready."
response_variable: result
```

Use `room` for one room or `rooms` for an explicit list. No private reply falls back to another room. Announcements respect quiet hours and reported busy state; intentional questions can still be answered. Queue acceptance is not playback confirmation.

The disabled-by-default `multiroom-greeting.example.yaml` shows optional occupancy-triggered greeting using a local motion sensor, not a camera or identity tracking. Configure the room, sensor, times and text. Legacy single-device camera greetings are not migrated. The example records daily acceptance, not confirmed playback. Automatic announcements may be skipped while a dashboard microphone is active, including wakeword mode.

## Validation required before release

Test two separate tablets/Echos, simultaneous requests, room isolation, player reconnect, Bluetooth loss, quiet hours, busy state, area-specific actions, and the legacy single-room path. Verify Android and HA CI. No production deployment, private dashboard changes, or GPU worker changes are part of this branch.
