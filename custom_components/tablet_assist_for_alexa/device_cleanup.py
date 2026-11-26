"""Remove only TAFA-owned device/entity registry entries during explicit deletion.

Never touch Home Assistant users, scripts, automations, or entities belonging
to other integrations. Room sessions and camera frames are revoked separately.
"""
from homeassistant.helpers import entity_registry as er, device_registry as dr
from .const import DOMAIN


def _cleanup(hass, identifier, expected_prefix):
    registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    device = registry.async_get_device(identifiers={(DOMAIN, identifier)})
    if device is None:
        return
    for entry in tuple(er.async_entries_for_device(entity_registry, device.id)):
        if entry.platform == DOMAIN and entry.unique_id.startswith(expected_prefix):
            entity_registry.async_remove(entry.entity_id)
    # Do not remove a shared device or unrelated entities.
    if (not er.async_entries_for_device(entity_registry, device.id)
            and len(device.config_entries) <= 1):
        registry.async_remove_device(device.id)


def cleanup_tablet(hass, identifier):
    _cleanup(hass, identifier, "tafa_" + identifier + "_")


def cleanup_room(hass, room):
    cameras = hass.data.get(DOMAIN, {}).get("room_cameras")
    if not cameras:
        return
    prefix = cameras.entry.entry_id + "_room_" + room
    _cleanup(hass, prefix, prefix + "_")
    cameras.forget_room(room)
