"""Scope native Home Assistant Assist light changes to the paired TAFA tablet.

Home Assistant executes local intents before the TAFA conversation entity. Native
lighting intents may resolve registry targets without a public call_service
event naming their entity IDs. Listen to both explicit service calls and the
resulting confirmed state changes, without executing any command ourselves.
"""
from time import monotonic

from homeassistant.const import EVENT_CALL_SERVICE, EVENT_STATE_CHANGED
from homeassistant.core import callback

from .const import DOMAIN
from .switch_notice_logic import (
    eligible_wake, expected_state, extract_targets, confirmed_transition,
)

KEY = "native_switch_notice"
WAKE_EVENT = "tafa_android_wakeword_routed"
NOTICE_EVENT = "tafa_infobox_show"


def setup_switch_intent_bridge(hass):
    data = hass.data.setdefault(DOMAIN, {})
    if KEY in data:
        return
    wakes = {}

    @callback
    def wake(event):
        raw = event.data
        if not isinstance(raw, dict):
            return
        device_id = raw.get("device_id")
        if not isinstance(device_id, str) or len(device_id) != 32:
            return
        controller = data.get("wake_devices_dynamic")
        audio = data.get("room_audio")
        device = getattr(controller, "devices", {}).get(device_id)
        if not isinstance(device, dict):
            return
        user_id = device.get("user_id")
        if not isinstance(user_id, str) or not user_id:
            return
        room = next((
            room for room, principal in getattr(audio, "rooms", {}).items()
            if principal == user_id
            and getattr(audio, "settings", {}).get(room, {}).get("wake_device_id") == device_id
        ), None)
        if not room:
            return
        # A new wake replaces older wakes for that user, not other active rooms.
        for identifier, route in list(wakes.items()):
            if route["user_id"] == user_id or monotonic() - route["at"] > 25:
                wakes.pop(identifier, None)
        wakes[device_id] = {
            "at": monotonic(), "user_id": user_id, "room": room,
            "device_id": device_id, "context_id": None, "seen": set(),
        }

    def route_for(context):
        principal = getattr(context, "user_id", None)
        context_id = getattr(context, "id", None)
        if not principal or not context_id or getattr(context, "parent_id", None):
            return None
        routes = [
            route for route in wakes.values()
            if eligible_wake(route, principal, monotonic(), context_id)
        ]
        return routes[0] if len(routes) == 1 else None

    def notify(route, entity_id, previous, desired, context, state):
        if entity_id in route["seen"] or desired not in ("on", "off"):
            return
        route["seen"].add(entity_id)
        route["context_id"] = context.id
        friendly = str(state.attributes.get("friendly_name") or entity_id)[:90]
        action = "einschalten" if desired == "on" else "ausschalten"
        hass.bus.async_fire(NOTICE_EVENT, {
            "template": "switch",
            "title": "TAFA · Schaltauftrag",
            "message": friendly + ": " + action,
            "entity_id": entity_id,
            "requested_state": desired,
            "previous_state": previous,
            "device_id": route["device_id"],
            "room": route["room"],
            "seconds": 12,
            "request_id": "native-" + context.id[:48] + "-" + entity_id[:40],
        }, context=context)

    @callback
    def service(event):
        payload = event.data
        if not isinstance(payload, dict):
            return
        ids = extract_targets(
            payload.get("domain"), payload.get("service"),
            payload.get("service_data", {}),
        )
        if not ids:
            return
        context = event.context
        route = route_for(context)
        if route is None:
            return
        for entity_id in ids:
            state = hass.states.get(entity_id)
            previous = getattr(state, "state", None)
            desired = expected_state(payload["service"], previous)
            if state is not None and desired is not None:
                notify(route, entity_id, previous, desired, context, state)

    @callback
    def state_changed(event):
        raw = event.data
        if not isinstance(raw, dict):
            return
        entity_id = raw.get("entity_id")
        old_state = raw.get("old_state")
        new_state = raw.get("new_state")
        previous = getattr(old_state, "state", None)
        desired = getattr(new_state, "state", None)
        if not confirmed_transition(entity_id, previous, desired):
            return
        # The *new entity state's* provenance is authoritative. This can
        # differ from the wrapper event's context for native Assist intents.
        context = getattr(new_state, "context", None) or event.context
        route = route_for(context)
        if route is None:
            return
        notify(route, entity_id, previous, desired, context, new_state)

    data[KEY] = (
        hass.bus.async_listen(WAKE_EVENT, wake),
        hass.bus.async_listen(EVENT_CALL_SERVICE, service),
        hass.bus.async_listen(EVENT_STATE_CHANGED, state_changed),
    )


def unload_switch_intent_bridge(hass):
    for unsub in hass.data.get(DOMAIN, {}).pop(KEY, ()):
        unsub()
