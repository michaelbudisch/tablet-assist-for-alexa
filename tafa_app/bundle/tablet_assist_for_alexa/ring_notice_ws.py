"""Pairing-scoped Ring movement notifications for TAFA dashboards.

No global event-bus access is granted to regular users, and camera mappings
are taken exclusively from this installation's TAFA configuration. No
recordings, signed URLs, descriptions or credentials are forwarded.
"""
import voluptuous as vol

from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .visual_ws import _paired_devices

COMMAND = DOMAIN + "/ring_notice_subscribe"
EVENT_TYPES = ("tafa_camera_notice", "jarvis_infobox_show")  # legacy compatibility


def _ring_cameras(hass, entry):
    """Only two explicitly configured Ring devices and their related views."""
    registry = er.async_get(hass)
    configured = (
        entry.options.get("vision_door_camera"),
        entry.options.get("vision_outside_camera"),
    )
    ids, devices = set(), set()
    for entity_id in configured:
        entity = registry.async_get(entity_id) if isinstance(entity_id, str) else None
        if (entity and entity.platform == "ring" and not entity.disabled_by
                and (entity.translation_key == "last_recording"
                     or str(entity.unique_id).endswith("-last_recording"))):
            ids.add(entity_id)
            if entity.device_id:
                devices.add(entity.device_id)
    if devices:
        for entity in registry.entities.values():
            if (entity.platform == "ring" and entity.device_id in devices
                    and entity.translation_key in ("last_recording", "live_view")
                    and not entity.disabled_by):
                ids.add(entity.entity_id)
    return frozenset(ids)


@websocket_api.websocket_command({vol.Required("type"): COMMAND})
@websocket_api.async_response
async def ring_notice_subscribe(hass, connection, msg):
    user = connection.user
    entries = hass.config_entries.async_entries(DOMAIN)
    data = hass.data.get(DOMAIN, {})
    controller, transport = data.get("wake_devices_dynamic"), data.get("room_audio")
    if (not user or not user.is_active or len(entries) != 1
            or controller is None or transport is None):
        connection.send_error(msg["id"], "not_ready", "TAFA device registry unavailable")
        return
    devices = _paired_devices(hass, user, controller, transport)
    if not devices:
        connection.send_error(msg["id"], "unauthorized", "No paired TAFA tablet")
        return

    allowed_ids = {d["device_id"] for d in devices}
    allowed_rooms = {d["room"].casefold() for d in devices} | {
        d["label"].casefold() for d in devices
    }

    @callback
    def on_ring(event):
        current = _paired_devices(hass, user, controller, transport)
        if not current:
            return
        permitted_ids = allowed_ids & {d["device_id"] for d in current}
        if not permitted_ids:
            return
        payload = event.data
        if not isinstance(payload, dict):
            return
        camera = payload.get("camera")
        if not isinstance(camera, str) or camera not in _ring_cameras(hass, entries[0]):
            return
        # The motion event may refer to the live-view sibling. Display the
        # last-recording camera instead, never starting a livestream.
        registry = er.async_get(hass)
        source = registry.async_get(camera)
        recording = camera
        for option in ("vision_door_camera", "vision_outside_camera"):
            candidate_id = entries[0].options.get(option)
            candidate = registry.async_get(candidate_id) if candidate_id else None
            if candidate and source and candidate.device_id == source.device_id:
                recording = candidate_id
                break
        if not user.is_admin and not user.permissions.check_entity(recording, POLICY_READ):
            return
        title = payload.get("title", "")
        if event.event_type == "jarvis_infobox_show" and (
            not isinstance(title, str) or not title.startswith("Ring · ")
        ):
            return
        routed_id = payload.get("device_id") or payload.get("target_device_id")
        routed_room = payload.get("room") or payload.get("target_room")
        if routed_id and routed_id not in permitted_ids:
            return
        if routed_room and (
            not isinstance(routed_room, str) or routed_room.casefold() not in allowed_rooms
        ):
            return
        request_id = payload.get("request_id")
        if not isinstance(request_id, str) or not 0 < len(request_id) <= 100:
            return
        try:
            duration = max(5, min(90, int(payload.get("seconds", 55))))
        except (TypeError, ValueError):
            duration = 55
        connection.send_event(msg["id"], {
            "title": title[:100] if isinstance(title, str) and title.startswith("Ring · ") else "Ring · Bewegung",
            "message": "Bewegung erkannt",
            "camera": recording,
            "seconds": duration,
            "request_id": request_id,
            "device_id": routed_id or "",
            "room": routed_room or "",
        })

    unsubscribers = [hass.bus.async_listen(name, on_ring) for name in EVENT_TYPES]
    def unsubscribe():
        for fn in unsubscribers:
            fn()
    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"], {"subscribed": True})
