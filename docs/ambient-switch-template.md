# TAFA switch-specific ambient infobox

The switch infobox is a distinct presentation template, not a new device-control mechanism. An explicit successful call to `script.tafa_geraet_schalten` can emit `tafa_infobox_show` with the fields below. The UI only marks a device **confirmed** when its current Home Assistant entity state matches the desired state; a service call alone is not evidence of success.

## Event / module contract

```yaml
event: tafa_infobox_show
event_data:
  title: TAFA · Schaltauftrag
  message: Wohnzimmerlicht einschalten
  template: switch
  entity_id: light.wohnzimmer
  requested_state: 'on'
  previous_state: 'off'
  seconds: 12
  room: wohnzimmer  # optional; specify for multiroom targeting
  device_id: ''   # optional: target one paired tablet
  request_id: 'switch-example-1'
```

The same payload can be sent via `tablet_assist_for_alexa.infobox_anzeigen` using `titel, nachricht, dauer` and the matching optional switch fields, after backend update. The private Hauszentrale dashboard displays it through `www/tafa/hauszentrale-main.js` → `www/tafa/ambient-night.js` → `www/tafa/ambient-switch.js`. Those private dashboard assets are not currently part of the public repository. Generic, Ring and knowledge cards remain separate.

Allowed entities: `light.*`, `switch.*`, `input_boolean.*`. `requested_state` must be `on` or `off`; `previous_state` may additionally be empty. Non-admin tablet streams enforce the normal entity-read permission before forwarding device metadata. `demo: true` provides a preview that **never** actuates the device or reports verified success.

Room-specific commands must pass `room` or `device_id`. An event without target uses TAFA's existing broadcast behavior to eligible subscribed screens. Native Assist light actions that do not use the TAFA switching script are not automatically intercepted.

## Native Assist voice commands

Since TAFA App 0.4.74 / integration 0.5.9, native Assist calls with `prefer_local_intents: true` are also observed. TAFA listens only after an authenticated `tafa_android_wakeword_routed` event for a paired tablet. Within a 25-second bounded window it correlates direct, root-context `call_service` events from the room's assigned Home Assistant user. Eligible calls must explicitly name at most six `light.*`, `switch.*`, or `input_boolean.*` entities and use `turn_on`, `turn_off`, or `toggle`; all other events are ignored.

The bridge publishes only presentation metadata to `tafa_infobox_show`. A native command continues to execute via Home Assistant (TAFA never repeats it). The ambient client confirms the requested state from the actual HA entity. Commands using area/device targets without explicit entity IDs are intentionally ignored rather than inferring or broadcasting arbitrary devices.

## Confirmed state-change fallback

TAFA App 0.4.75 (integration 0.5.10) additionally observes `state_changed` for **actual on/off transitions** where the new entity state's root context belongs to the paired TAFA user during the recent wake window. This complements explicit service events, since native HA intents may resolve entity targets internally. An entity change produces at most one scoped notice per wake/request context; non-TAFA manual and automated changes are ignored. No-op commands that do not change state may be speech-only.
