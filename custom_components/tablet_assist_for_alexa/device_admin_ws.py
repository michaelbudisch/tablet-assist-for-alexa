"""Administrator-only HA WebSocket bridge for TAFA's Supervisor Control Center.

Native Android REST voice/audio routes remain unchanged. Supervisor settings
use the authenticated HA WebSocket, matching existing TAFA app configuration.
"""
import re
import voluptuous as vol
from homeassistant.components import websocket_api
from .const import DOMAIN
from .device_cleanup import cleanup_tablet, cleanup_room

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
                  "camera_online": bool(data.get("room_cameras") and
                                        data["room_cameras"].store.fresh(name)),
                  **transport.status(owner)}
                 for name, owner in transport.rooms.items()]
        return {"users": sorted(users, key=lambda u: u["name"].casefold()),
                "devices": sorted(devices, key=lambda d: (d["room"].casefold(), d["device_id"])),
                "rooms": sorted(rooms, key=lambda r: r["room"])}
    if action == "delete_device":
        if msg.get("confirmed") is not True:
            raise ValueError("Explicit confirmation required")
        identifier = msg.get("device_id")
        if not isinstance(identifier, str) or not DEVICE_ID.fullmatch(identifier):
            raise ValueError("Invalid tablet ID")
        if identifier not in controller.devices:
            raise ValueError("Tablet is not registered")
        # Unbind all rooms before deleting the HA registration. End active
        # audio and camera sessions but preserve every HA user and room.
        for assigned, settings in tuple(transport.settings.items()):
            if settings.get("wake_device_id") == identifier and assigned in transport.rooms:
                principal = transport.rooms[assigned]
                transport.revoke(assigned)
                transport.provision(assigned, principal)
                transport.settings[assigned] = {
                    **{key: value for key, value in settings.items()
                       if key != "wake_device_id"},
                    "camera_enabled": False,
                }
        await persist()
        await controller.handle(user, "delete", identifier, {})
        cleanup_tablet(hass, identifier)
        return {"device_id": identifier, "removed": True}
    if action == "camera_diagnostics":
        # Read-only administrator troubleshooting; no user IDs or tokens
        # in the response. Never alter room, pairing or camera consent here.
        identifier = msg.get("device_id")
        if not isinstance(identifier, str) or not DEVICE_ID.fullmatch(identifier):
            raise ValueError("Invalid device")
        device = controller.devices.get(identifier)
        if not device:
            raise ValueError("Tablet not enrolled")
        principal = device.get("user_id")
        owner = await hass.auth.async_get_user(principal) if principal else None
        assigned_rooms = [room for room, user_id in transport.rooms.items()
                          if user_id == principal]
        return {
            "enrolled": True,
            "owner_active": bool(owner and owner.is_active),
            "owner_admin": bool(owner and owner.is_admin),
            "owner_system": bool(owner and owner.system_generated),
            "assigned_rooms": [
                {"room": room,
                 "paired_to_this_tablet": transport.settings.get(room, {}).get("wake_device_id") == identifier,
                 "paired_to_another_tablet": bool(transport.settings.get(room, {}).get("wake_device_id") not in ("", None, identifier)),
                 "camera_enabled": transport.settings.get(room, {}).get("camera_enabled") is True,
                 "online": bool(transport.status(principal).get("online"))}
                for room in assigned_rooms
            ],
        }
    if action == "camera_setup":
        # Explicit one-shot migration for an already enrolled tablet.
        # Derive the actual HA user from its registered owner; never trust a
        # client-supplied principal or reassign ownership during migration.
        identifier, room = msg.get("device_id"), msg.get("room")
        if not isinstance(identifier, str) or not DEVICE_ID.fullmatch(identifier):
            raise ValueError("Invalid device")
        if not isinstance(room, str) or not ROOM.fullmatch(room):
            raise ValueError("Invalid room")
        device = controller.devices.get(identifier)
        if device is None:
            raise ValueError("Tablet not enrolled")
        principal = device.get("user_id")
        owner = await hass.auth.async_get_user(principal) if principal else None
        if not owner or not owner.is_active or owner.is_admin or owner.system_generated:
            raise ValueError("Tablet needs a dedicated active HA user")
        if any(r != room and p == principal for r, p in transport.rooms.items()):
            raise ValueError("HA user is already assigned to a different room")
        if room in transport.rooms and transport.rooms[room] != principal:
            raise ValueError("Room belongs to another HA user")
        if any(r != room and s.get("wake_device_id") == identifier
               for r, s in transport.settings.items()):
            raise ValueError("Tablet already paired to another room")
        associated = transport.settings.get(room, {}).get("wake_device_id")
        if associated and associated != identifier:
            raise ValueError("Room paired to another tablet")
        if room not in transport.rooms:
            transport.provision(room, principal)
        transport.settings[room] = {**transport.settings.get(room, {}),
                                    "wake_device_id": identifier,
                                    "camera_enabled": True}
        await persist()
        return {"room": room, "paired": True, "camera_enabled": True}
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
    # A room can still be deleted when its former HA user has been
    # disabled/deleted. Ownership must match the persisted room record.
    if action in ("unpair", "delete_room"):
        if msg.get("confirmed") is not True:
            raise ValueError("Explicit confirmation required")
        if transport.rooms.get(room) != principal:
            raise ValueError("Room or ownership changed")
        if action == "unpair":
            identifier = msg.get("device_id")
            if (not isinstance(identifier, str) or not DEVICE_ID.fullmatch(identifier)
                    or transport.settings.get(room, {}).get("wake_device_id") != identifier):
                raise ValueError("Tablet pairing already changed")
            settings = transport.settings.get(room, {})
            transport.revoke(room)
            transport.provision(room, principal)
            transport.settings[room] = {
                **{key: value for key, value in settings.items()
                   if key != "wake_device_id"},
                "camera_enabled": False,
            }
            await persist()
            return {"room": room, "unpaired": True}
        transport.revoke(room)
        transport.settings.pop(room, None)
        await persist()
        cleanup_room(hass, room)
        return {"room": room, "removed": True}
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
    vol.Required("action"): vol.In(("list", "create", "pair", "configure", "camera", "camera_setup", "camera_diagnostics",
                        "unpair", "delete_device", "delete_room")),
    vol.Optional("room"): str,
    vol.Optional("user_id"): str,
    vol.Optional("device_id"): str,
    vol.Optional("transfer_device"): bool,
    vol.Optional("camera_enabled"): bool,
    vol.Optional("confirmed"): bool,
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
