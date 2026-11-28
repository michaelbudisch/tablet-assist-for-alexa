"""Admin-only configuration for TAFA Ring recording camera mappings.

TAFA's App-managed installation does not expose the old integration options
flow. This command saves just the two vision mappings, retaining all the
Supervisor App's unrelated settings and pairing data. The App sync merges
options non-destructively and thus preserves these keys.
"""
import re

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

COMMAND = DOMAIN + "/vision_camera_config"
KEYS = ("vision_door_camera", "vision_outside_camera")
CAMERA_ID = re.compile(r"^camera\.[a-z0-9_]+$")


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): COMMAND,
    vol.Required("action"): vol.In(("get", "set")),
    vol.Optional("door_camera"): str,
    vol.Optional("outside_camera"): str,
})
@websocket_api.async_response
async def vision_camera_config(hass, connection, msg):
    entries = hass.config_entries.async_entries(DOMAIN)
    if len(entries) != 1:
        connection.send_error(msg["id"], "not_ready", "Exactly one TAFA integration required")
        return
    entry = entries[0]
    before = {
        "door_camera": entry.options.get(KEYS[0], ""),
        "outside_camera": entry.options.get(KEYS[1], ""),
    }
    if msg["action"] == "get":
        connection.send_result(msg["id"], {**before, "managed_by": "TAFA"})
        return
    door = msg.get("door_camera")
    outside = msg.get("outside_camera")
    if not isinstance(door, str) or not isinstance(outside, str):
        connection.send_error(msg["id"], "invalid_camera", "Both Ring camera entities are required")
        return
    if door == outside or not CAMERA_ID.fullmatch(door) or not CAMERA_ID.fullmatch(outside):
        connection.send_error(msg["id"], "invalid_camera", "Choose two different camera entities")
        return
    registry = er.async_get(hass)
    for camera in (door, outside):
        entity = registry.async_get(camera)
        state = hass.states.get(camera)
        if not state or state.state in ("unknown", "unavailable") or (entity is not None and entity.disabled_by):
            connection.send_error(msg["id"], "invalid_camera", "Camera is not available: " + camera)
            return
        # Ring refreshes video_url only while a recording exists. Validate the
        # stable registry identity instead of rejecting a camera after reboot.
        if not entity or entity.platform != "ring" or not (
            entity.translation_key == "last_recording"
            or str(entity.unique_id).endswith("-last_recording")
        ):
            connection.send_error(msg["id"], "not_recording_camera", "Choose the Ring last-recording camera: " + camera)
            return
    updated = dict(entry.options)
    updated[KEYS[0]] = door
    updated[KEYS[1]] = outside
    changed = updated != entry.options
    if changed:
        hass.config_entries.async_update_entry(entry, options=updated)
    connection.send_result(msg["id"], {
        "changed": changed, "door_camera": door, "outside_camera": outside,
        "managed_by": "TAFA",
    })
