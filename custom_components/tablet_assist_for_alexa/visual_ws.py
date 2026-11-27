"""Read-only, room-authorized visual response stream for TAFA dashboards.

This avoids granting ordinary room users access to the global HA event bus
while allowing a paired tablet to receive its own Assist answer. Admins
can subscribe; their dashboards still filter to the locally bound device.
"""
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import callback

from .const import DOMAIN

COMMAND = DOMAIN + "/visual_subscribe"


@websocket_api.websocket_command({vol.Required("type"): COMMAND})
@websocket_api.async_response
async def visual_subscribe(hass, connection, msg):
    user = connection.user
    if not user or not user.is_active:
        connection.send_error(msg["id"], "unauthorized", "User is not active")
        return

    data = hass.data.get(DOMAIN, {})
    controller = data.get("wake_devices_dynamic")
    transport = data.get("room_audio")
    if controller is None or transport is None:
        connection.send_error(msg["id"], "not_ready", "TAFA room bridge not loaded")
        return

    if not user.is_admin:
        owned = {identifier for identifier, device in controller.devices.items()
                 if device.get("user_id") == user.id}
        authorized = any(principal == user.id
                         and transport.settings.get(room, {}).get("wake_device_id") in owned
                         for room, principal in transport.rooms.items())
        if not authorized:
            connection.send_error(msg["id"], "unauthorized", "No paired TAFA room")
            return

    @callback
    def on_reply(event):
        payload = event.data
        if not isinstance(payload, dict) or not isinstance(payload.get("reply"), str):
            return
        if not payload["reply"].strip():
            return
        # Non-admin clients receive only answers from their own room account.
        if not user.is_admin and payload.get("user_id") != user.id:
            return
        connection.send_event(msg["id"], payload)

    unsubscribe = hass.bus.async_listen("tafa_assist_response", on_reply)
    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"], {"subscribed": True})
