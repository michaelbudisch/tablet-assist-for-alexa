"""Bridge successful native Assist switch calls to typed TAFA ambient notices.

Native Assist commands are evaluated by Home Assistant before TAFA's conversation
agent when prefer_local_intents is enabled. This listener does not alter that
pipeline or execute any device command. It correlates an authenticated native
wakeword with direct, user-attributed service calls for named entities only.
"""
from time import monotonic

from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import callback

from .const import DOMAIN
from .switch_notice_logic import eligible_wake, expected_state, extract_targets

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
        now = monotonic()
        wakes.clear()  # A new native wake supersedes previous routing.
        wakes[device_id] = {"at": now, "user_id": user_id, "room": room,
                            "device_id": device_id, "context_id": None,
                            "seen": set()}

    @callback
    def service(event):
        payload = event.data
        if not isinstance(payload, dict):
            return
        service_domain = payload.get("domain")
        service_name = payload.get("service")
        ids = extract_targets(service_domain, service_name,
                              payload.get("service_data", {}))
        if not ids:
            return
        context = event.context
        principal = getattr(context, "user_id", None)
        context_id = getattr(context, "id", None)
        # Script and automation chains have their own notification mechanism.
        # Direct native Assist commands carry a root user context.
        if not principal or not context_id or getattr(context, "parent_id", None):
            return
        now = monotonic()
        matching = [w for w in wakes.values()
                    if eligible_wake(w, principal, now, context_id)]
        if len(matching) != 1:
            return
        route = matching[0]
        for entity_id in ids:
            state = hass.states.get(entity_id)
            previous = getattr(state, "state", None)
            desired = expected_state(service_name, previous)
            if desired is None or entity_id in route["seen"]:
                continue
            route["seen"].add(entity_id)
            route["context_id"] = context_id
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
                "request_id": "native-" + context_id[:48] + "-" + entity_id[:40],
            }, context=context)

    data[KEY] = (hass.bus.async_listen(WAKE_EVENT, wake),
                 hass.bus.async_listen(EVENT_CALL_SERVICE, service))


def unload_switch_intent_bridge(hass):
    for unsub in hass.data.get(DOMAIN, {}).pop(KEY, ()):
        unsub()
