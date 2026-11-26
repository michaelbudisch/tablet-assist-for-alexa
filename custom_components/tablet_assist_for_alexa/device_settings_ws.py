"""Authenticated, per-tablet HA WebSocket push for native microphone settings.

Only the owner of an enrolled tablet (or an HA administrator) can subscribe.
No tokens, audio, room assignments or personal data are pushed. On
disconnect the Android client falls back to authenticated REST polling.
"""
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .relay.relay_wake_devices import KEY, SETTINGS_SIGNAL

COMMAND = DOMAIN + "/device_settings_subscribe"


def settings_payload(device):
    return {
        "device_id": device["device_id"],
        "muted": device.get("muted", False),
        "voice_mode": device.get("voice_mode", "wake"),
        "followup_limit": device.get("followup_limit", -1),
        "word": device.get("word", "Hey Jarvis"),
        "mic_gain": device.get("mic_gain", 100),
        "strict": device.get("strict", 1),
        "cooldown": device.get("cooldown", 12),
        "hold": device.get("hold", 50),
        "pause_ms": device.get("pause_ms", 1700),
    }


@websocket_api.websocket_command({
    vol.Required("type"): COMMAND,
    vol.Required("device_id"): vol.Match(r"^[a-f0-9]{32}$"),
})
@websocket_api.async_response
async def device_settings_subscribe(hass, connection, msg):
    controller = hass.data.get(DOMAIN, {}).get(KEY)
    if controller is None:
        connection.send_error(msg["id"], "not_ready", "TAFA device service unavailable")
        return
    user = connection.user
    identifier = msg["device_id"]
    device = controller.devices.get(identifier)
    if (not user or not user.is_active or not device
            or not controller.allowed(user, device)):
        connection.send_error(msg["id"], "unauthorized", "Unknown or unauthorized device")
        return

    def on_device_change(changed_id):
        if changed_id != identifier:
            return
        current = controller.devices.get(identifier)
        if not current or not controller.allowed(user, current):
            return
        connection.send_event(msg["id"], settings_payload(current))

    unsubscribe = async_dispatcher_connect(hass, SETTINGS_SIGNAL, on_device_change)
    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"], {"subscribed": True})
    on_device_change(identifier)
