"""Administrator-only HA WebSocket bridge for TAFA's Supervisor Control Center.

Native Android REST voice/audio routes remain unchanged. Supervisor settings
use the authenticated HA WebSocket, matching existing TAFA app configuration.
"""
import re
import voluptuous as vol
from homeassistant.components import websocket_api
from .const import DOMAIN

COMMAND = DOMAIN + "/device_admin"
DEVICE_ID = re.compile(r"[a-f0-9]{32}\Z")
ROOM = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")


async def perform_device_admin(hass, user, msg):
    if not user or not user.is_active or not user.is_admin:
        raise PermissionError("Administrator required")
    data = hass.data.get(DOMAIN, {})
    controller = data.get("wake_devices_dynamic")
    transport = data.get("room_audio")
    persist = data.get("room_audio_save")
    if controller is None or transport is None or persist is None:
        raise RuntimeError("Native TAFA backend not loaded")
    action = msg["action"]
    if action == "list":
        users = [{"id": u.id, "name": u.name or u.id}
                 for u in await hass.auth.async_get_users()
                 if u.is_active and not u.is_admin and not u.system_generated]
        async with controller.lock:
            devices = [controller.public(d) for d in controller.devices.values()]
        rooms = [{"room": name, "user_id": owner,
                  "wake_device_id": transport.settings.get(name, {}).get("wake_device_id", ""),
                  "camera_enabled": transport.settings.get(name, {}).get("camera_enabled") is True,
                  **transport.status(owner)}
                 for name, owner in transport.rooms.items()]
        return {"users": sorted(users, key=lambda u: u["name"].casefold()),
                "devices": sorted(devices, key=lambda d: (d["room"].casefold(), d["device_id"])),
                "rooms": sorted(rooms, key=lambda r: r["room"])}
    if action == "configure":
        identifier = msg.get("device_id")
        if not isinstance(identifier, str) or not DEVICE_ID.fullmatch(identifier):
            raise ValueError("Invalid tablet ID")
        result = await controller.handle(user, "configure", identifier,
                                         {"settings": msg.get("settings")})
        return {"device": result["device"]}
    room, principal = msg.get("room"), msg.get("user_id")
    if (not isinstance(room, str) or not ROOM.fullmatch(room)
            or not isinstance(principal, str) or not 1 <= len(principal) <= 128):
        raise ValueError("Invalid room or user")
    selected = await hass.auth.async_get_user(principal)
    if (not selected or not selected.is_active or selected.is_admin
            or selected.system_generated):
        raise ValueError("Dedicated non-admin HA user required")
    if action == "create":
        if room in transport.rooms or principal in transport.rooms.values():
            raise ValueError("Room or assigned HA user already exists")
        transport.provision(room, principal)
        await persist()
        return {"room": room, "created": True}
    if action == "camera":
        # Only an administrator may explicitly enable one enrolled room's
        # camera uploads. Disabling also clears existing in-memory frames via
        # persist() -> room camera hub sync().
        enabled = msg.get("camera_enabled")
        if type(enabled) is not bool or transport.rooms.get(room) != principal:
            raise ValueError("Invalid room camera setting")
        transport.settings[room] = {
            **transport.settings.get(room, {}),
            "camera_enabled": enabled,
        }
        await persist()
        return {"room": room, "camera_enabled": enabled}
    if action == "pair":
        identifier = msg.get("device_id")
        transfer = msg.get("transfer_device", False)
        if (not isinstance(identifier, str) or not DEVICE_ID.fullmatch(identifier)
                or type(transfer) is not bool):
            raise ValueError("Invalid device or transfer choice")
        device = controller.devices.get(identifier)
        if not device:
            raise ValueError("Tablet is not enrolled")
        if transport.rooms.get(room) != principal:
            raise ValueError("Create the room for this user first")
        if device.get("user_id") != principal and not transfer:
            raise ValueError("Confirm tablet ownership transfer")
        if any(r != room and settings.get("wake_device_id") == identifier
               for r, settings in transport.settings.items()):
            raise ValueError("Tablet already assigned to a different room")
        existing = transport.settings.get(room, {}).get("wake_device_id")
        if existing and existing != identifier:
            raise ValueError("Room already paired to a different tablet")
        transport.settings[room] = {**transport.settings.get(room, {}),
                                    "wake_device_id": identifier}
        await persist()
        if device.get("user_id") != principal:
            async with controller.lock:
                controller.devices[identifier]["user_id"] = principal
                await controller.save()
                controller.changed(identifier)
        return {"room": room, "paired": True}
    raise ValueError("Invalid device action")


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): COMMAND,
    vol.Required("action"): vol.In(("list", "create", "pair", "configure", "camera")),
    vol.Optional("room"): str,
    vol.Optional("user_id"): str,
    vol.Optional("device_id"): str,
    vol.Optional("transfer_device"): bool,
    vol.Optional("camera_enabled"): bool,
    vol.Optional("settings"): dict,
})
@websocket_api.async_response
async def device_admin_command(hass, connection, msg):
    try:
        result = await perform_device_admin(hass, connection.user, msg)
    except PermissionError:
        connection.send_error(msg["id"], "unauthorized", "Administrator required")
        return
    except (ValueError, TypeError, KeyError):
        connection.send_error(msg["id"], "invalid_request", "Invalid room or tablet")
        return
    except RuntimeError:
        connection.send_error(msg["id"], "not_ready", "TAFA backend not loaded")
        return
    connection.send_result(msg["id"], result)
