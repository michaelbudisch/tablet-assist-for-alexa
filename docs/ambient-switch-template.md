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
