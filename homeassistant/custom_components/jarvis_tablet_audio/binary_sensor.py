"""Optional coarse tablet image movement; unavailable when not enabled or image stale."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .relay_camera import runtime

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RelayMotion(runtime(hass), entry)])

class RelayMotion(BinarySensorEntity):
    _attr_name = "Echo Relay Bildbewegung"
    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_should_poll = False
    def __init__(self, relay, entry):
        self.relay = relay
        self._attr_unique_id = entry.entry_id + "_relay_motion"

    @property
    def available(self):
        return self.relay.frames.fresh and self.relay.frames.motion is not None

    @property
    def is_on(self):
        return self.relay.frames.motion is True

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.relay.listeners.add(self.async_write_ha_state)
        self.async_on_remove(lambda: self.relay.listeners.discard(self.async_write_ha_state))
