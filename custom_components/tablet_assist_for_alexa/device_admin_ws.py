"""Administrator-only HA WebSocket bridge for TAFA's Supervisor Control Center.

Native Android REST voice/audio routes remain unchanged. Supervisor settings
use the authenticated HA WebSocket, matching existing TAFA app configuration.
"""
import re
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.helpers import area_registry as ar, device_registry as dr
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
        registry = ar.async_get(hass)
        areas = [{"area_id": a.id, "name": a.name}
                 for a in registry.async_list_areas()]
        users = [{"id": u.id, "name": u.name or u.id}
                 for u in await hass.auth.async_get_users()
                 if u.is_active and not u.is_admin and not u.system_generated]
        async with controller.lock:
            devices = [controller.public(d) for d in controller.devices.values()]
        rooms = [{"room": name, "area_id": transport.settings.get(name, {}).get("area_id", name),
                  "device_name": controller.devices.get(transport.settings.get(name, {}).get("wake_device_id"), {}).get("room", ""),
                  "user_id": owner,
                  "wake_device_id": transport.settings.get(name, {}).get("wake_device_id", ""),
                  "camera_enabled": transport.settings.get(name, {}).get("camera_enabled") is True,
                  "camera_online": bool(data.get("room_cameras") and
                                        data["room_cameras"].store.fresh(name)),
                  **transport.status(owner)}
                 for name, owner in transport.rooms.items()]
        return {"users": sorted(users, key=lambda u: u["name"].casefold()),
                "devices": sorted(devices, key=lambda d: (d["room"].casefold(), d["device_id"])),
                "rooms": sorted(rooms, key=lambda r: r["room"]),
                "areas": sorted(areas, key=lambda a: a["name"].casefold())}
    if action == "assign_area":
        # HA Areas are grouping metadata; audio/camera connections remain
        # isolated by the owning non-admin HA principal and their unique route.
        identifier, area_id = msg.get("device_id"), msg.get("area_id")
        if (not isinstance(identifier, str) or not DEVICE_ID.fullmatch(identifier)
                or not isinstance(area_id, str) or not ROOM.fullmatch(area_id)):
            raise ValueError("Invalid tablet ID or Home Assistant area")
        area = ar.async_get(hass).async_get_area(area_id)
        if area is None:
            raise ValueError("Home Assistant area not found")
        device = controller.devices.get(identifier)
        if device is None:
            raise ValueError("Tablet is not registered")
        principal = device.get("user_id")
        owner = await hass.auth.async_get_user(principal) if principal else None
        if not owner or not owner.is_active or owner.is_admin or owner.system_generated:
            raise ValueError("Tablet requires a dedicated active non-admin HA user")

        # A single HA Area may contain multiple tablets. Each authenticates
        # separately: never merge principals or put two devices in one session.
        routes = [r for r, p in transport.rooms.items() if p == principal]
        if len(routes) > 1:
            raise ValueError("Dedicated HA user is already assigned more than one audio route")
        current = routes[0] if routes else None
        prior = transport.settings.get(current, {}) if current else {}
        previous_id = prior.get("wake_device_id")
        replaced_offline = bool(previous_id and previous_id != identifier)
        if replaced_offline:
            old = controller.devices.get(previous_id)
            if old and (old.get("user_id") != principal or controller.public(old).get("online")):
                raise ValueError("This HA user already owns an active tablet. Use a separate account for each tablet")
        if any(r != current and settings.get("wake_device_id") == identifier
               for r, settings in transport.settings.items()):
            raise ValueError("Tablet already assigned to a different audio route")
        previous_area = (prior.get("area_id") or current or "") if current else ""
        moved = bool(current and previous_area != area_id)
        if moved and msg.get("confirm_move") is not True:
            raise ValueError("Moving an existing tablet needs explicit confirmation")

        # Retain the original route for existing installations. The first new
        # tablet in a room can use its HA area as a legacy-compatible route.
        # Additional tablets use stable, per-installation internal route IDs.
        if current and not moved:
            route = current
        elif current and current.startswith("tafa_"):
            route = current
        elif area_id not in transport.rooms or area_id == current:
            route = area_id
        else:
            route = "tafa_" + identifier
        if route in transport.rooms and route != current:
            raise ValueError("Reserved audio route already belongs to a different tablet")
        if current != route:
            if current:
                transport.revoke(current)
                transport.settings.pop(current, None)
            transport.provision(route, principal)
        transport.settings[route] = {
            **(prior if current else {}),
            "wake_device_id": identifier,
            "area_id": area_id,
            "camera_enabled": bool(prior.get("camera_enabled")) if not moved else False,
        }
        await persist()
        if current and route != current:
            cleanup_room(hass, current)
        registry = dr.async_get(hass)
        # Avoid deprecated async_get_device() on HA 2026.11+.
        actual = registry.async_get_device_by_identifier(DOMAIN, identifier)
        if actual and actual.area_id != area_id:
            registry.async_update_device(actual.id, area_id=area_id)
        return {"room": area_id, "area": area.name, "device_id": identifier,
                "paired": True, "moved": moved, "audio_route": route,
                "replaced_offline": replaced_offline}
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
    if action == "migrate_legacy_vision":
        # One-time, opt-in config-entry transfer before deleting the old
        # integration. No network or model changes, no secrets, no agent swap.
        legacy = hass.config_entries.async_entries("jarvis_tablet_audio")
        current = hass.config_entries.async_entries(DOMAIN)
        if len(legacy) != 1 or len(current) != 1:
            raise ValueError("Expected one old and one new integration")
        from .relay.relay_models import VISION_MODELS, KEEP_ALIVE, CONTEXTS
        allowed = {"vision_model": VISION_MODELS,
                   "model_keep_alive": KEEP_ALIVE,
                   "model_num_ctx": CONTEXTS}
        values = {}
        for name, choices in allowed.items():
            value = legacy[0].options.get(name)
            if name not in current[0].options and type(value) in (str, int) and value in choices:
                values[name] = value
        if values:
            hass.config_entries.async_update_entry(
                current[0], options={**current[0].options, **values})
        return {"migrated": bool(values), "fields": sorted(values)}
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
    vol.Required("action"): vol.In(("list", "create", "pair", "assign_area", "configure", "camera", "camera_setup", "camera_diagnostics", "migrate_legacy_vision",
                        "unpair", "delete_device", "delete_room")),
    vol.Optional("room"): str,
    vol.Optional("area_id"): str,
    vol.Optional("confirm_move"): bool,
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
