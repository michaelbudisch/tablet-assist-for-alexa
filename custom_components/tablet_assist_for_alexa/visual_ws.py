"""Read-only, user- and device-scoped visual identity and response stream.

Regular HA room users may read ONLY their paired devices and their own
responses. Administrators may inspect all devices, but frontend desktops
do not auto-bind to them. No permanent speech text, token or room data
is stored by these endpoints.
"""
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

STREAM_COMMAND = DOMAIN + "/visual_subscribe"
IDENTITY_COMMAND = DOMAIN + "/visual_identity"


def _paired_devices(hass, user, controller, transport):
    registry = er.async_get(hass)
    devices = []
    for room, principal in transport.rooms.items():
        if not user.is_admin and principal != user.id:
            continue
        device_id = transport.settings.get(room, {}).get("wake_device_id", "")
        device = controller.devices.get(device_id)
        if not device or device.get("user_id") != principal:
            continue
        prefix = "tafa_" + device_id + "_"
        sensor_id = lambda key: registry.async_get_entity_id(
            "sensor", DOMAIN, prefix + key) or ""
        devices.append({
            "device_id": device_id,
            "room": room,
            "label": device.get("room") or room,
            "user_id": principal,
            "sensors": {
                "status": sensor_id("wake_status"),
                "mic": sensor_id("microphone"),
                "last": sensor_id("last_wake"),
            },
        })
    return devices


def _source_device_id(transport, controller, user_id):
    # Room audio requires a unique HA user per room. When ambiguous,
    # refuse to guess the source of a voice reply.
    matches = []
    for room, owner in transport.rooms.items():
        if not user_id or owner != user_id:
            continue
        device_id = transport.settings.get(room, {}).get("wake_device_id", "")
        device = controller.devices.get(device_id)
        if device and device.get("user_id") == owner:
            matches.append(device_id)
    return matches[0] if len(matches) == 1 else ""


@websocket_api.websocket_command({vol.Required("type"): IDENTITY_COMMAND})
@websocket_api.async_response
async def visual_identity(hass, connection, msg):
    user = connection.user
    if not user or not user.is_active:
        connection.send_error(msg["id"], "unauthorized", "User is not active")
        return
    data = hass.data.get(DOMAIN, {})
    controller, transport = data.get("wake_devices_dynamic"), data.get("room_audio")
    if controller is None or transport is None:
        connection.send_error(msg["id"], "not_ready", "TAFA device bridge unavailable")
        return
    connection.send_result(msg["id"], {
        "devices": _paired_devices(hass, user, controller, transport),
    })


@websocket_api.websocket_command({vol.Required("type"): STREAM_COMMAND})
@websocket_api.async_response
async def visual_subscribe(hass, connection, msg):
    user = connection.user
    if not user or not user.is_active:
        connection.send_error(msg["id"], "unauthorized", "User is not active")
        return

    data = hass.data.get(DOMAIN, {})
    controller, transport = data.get("wake_devices_dynamic"), data.get("room_audio")
    if controller is None or transport is None:
        connection.send_error(msg["id"], "not_ready", "TAFA device bridge unavailable")
        return
    if not user.is_admin and not _paired_devices(hass, user, controller, transport):
        connection.send_error(msg["id"], "unauthorized", "No paired TAFA room")
        return

    @callback
    def on_reply(event):
        payload = event.data
        if not isinstance(payload, dict) or not isinstance(payload.get("reply"), str):
            return
        if not payload["reply"].strip():
            return
        # Admin sockets receive events but each desktop still applies its
        # explicit display binding. Room users receive only their own.
        if not user.is_admin and payload.get("user_id") != user.id:
            return
        device_id = _source_device_id(transport, controller, payload.get("user_id"))
        tagged = {**payload, "tafa_device_id": device_id}
        connection.send_event(msg["id"], tagged)

    unsubscribe = hass.bus.async_listen("tafa_assist_response", on_reply)
    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"], {"subscribed": True})
