"""Scoped TAFA infobox notifications for paired dashboard tablets.

The bus remains private to Home Assistant. Unprivileged clients receive
only bounded presentation fields for their paired TAFA devices, with camera
access checked against Home Assistant's normal entity permissions.
"""
import re
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import callback
from homeassistant.auth.permissions.const import POLICY_READ
from .const import DOMAIN
from .visual_ws import _paired_devices

COMMAND = DOMAIN + "/notice_subscribe"
CAMERA_ID = re.compile(r"^camera\.[a-z0-9_]+$")


@websocket_api.websocket_command({vol.Required("type"): COMMAND})
@websocket_api.async_response
async def notice_subscribe(hass, connection, msg):
    user = connection.user
    data = hass.data.get(DOMAIN, {})
    controller = data.get("wake_devices_dynamic")
    transport = data.get("room_audio")
    if not user or not user.is_active or controller is None or transport is None:
        connection.send_error(msg["id"], "not_ready", "TAFA device registry unavailable")
        return
    devices = _paired_devices(hass, user, controller, transport)
    if not devices:
        connection.send_error(msg["id"], "unauthorized", "No paired TAFA device")
        return

    @callback
    def on_notice(event):
        current = _paired_devices(hass, user, controller, transport)
        if not current:
            return
        raw = event.data
        if not isinstance(raw, dict):
            return
        title, message = raw.get("title"), raw.get("message")
        if not isinstance(title, str) or not isinstance(message, str):
            return
        if not (0 < len(title) <= 100 and len(message) <= 2000):
            return
        target_id = raw.get("device_id")
        target_room = raw.get("room")
        if target_id and target_id not in {d["device_id"] for d in current}:
            return
        rooms = {d["room"].casefold() for d in current} | {
            d["label"].casefold() for d in current
        }
        if target_room and (not isinstance(target_room, str)
                            or target_room.casefold() not in rooms):
            return
        camera = raw.get("camera") or ""
        if camera:
            if not isinstance(camera, str) or not CAMERA_ID.fullmatch(camera):
                return
            if not user.is_admin and not user.permissions.check_entity(camera, POLICY_READ):
                return
        try:
            seconds = max(5, min(180, int(raw.get("seconds", 30))))
        except (TypeError, ValueError):
            seconds = 30
        request_id = str(raw.get("request_id") or "")[:100]
        connection.send_event(msg["id"], {
            "title": title, "message": message, "camera": camera,
            "seconds": seconds, "request_id": request_id,
            "device_id": target_id or "", "room": target_room or "",
        })

    unsub = hass.bus.async_listen("tafa_infobox_show", on_notice)
    connection.subscriptions[msg["id"]] = unsub
    connection.send_result(msg["id"], {"subscribed": True})
