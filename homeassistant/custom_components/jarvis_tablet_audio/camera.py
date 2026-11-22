"""Memory-only tablet camera with strict freshness."""
from homeassistant.components.camera import Camera
from .relay_camera import runtime

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RelayCamera(runtime(hass), entry)])

class RelayCamera(Camera):
    _attr_name = "Echo Relay Tablet"
    _attr_should_poll = False
    _attr_content_type = "image/jpeg"
    def __init__(self, relay, entry):
        super().__init__()
        self.relay = relay
        self._attr_unique_id = entry.entry_id + "_relay_camera"

    @property
    def available(self):
        return self.relay.frames.fresh

    @property
    def extra_state_attributes(self):
        return {"captured_at_ms": self.relay.frames.captured_at if self.available else None,
                "received_sequence": self.relay.frames.sequence if self.available else None,
                "image_interval_seconds": 2, "max_image_age_seconds": 15}

    async def async_camera_image(self, width=None, height=None):
        return self.relay.frames.image if self.available else None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.relay.listeners.add(self.async_write_ha_state)
        self.async_on_remove(lambda: self.relay.listeners.discard(self.async_write_ha_state))
