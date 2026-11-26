"""Common HA tablet entity identifiers, ownership and dynamic registration."""
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN
from .relay.relay_wake_devices import KEY, SIGNAL, REGISTERED_SIGNAL

class TabletMixin:
    _attr_has_entity_name = True

    def __init__(self, controller, device_id, key, label):
        self.controller = controller
        self.device_id = device_id
        self.key = key
        self._attr_unique_id = "tafa_" + device_id + "_" + key
        self._attr_name = label

    @property
    def device_info(self):
        room = self.controller.devices.get(self.device_id, {}).get("room", "Tablet")
        return {"identifiers": {(DOMAIN, self.device_id)},
                "name": "TAFA · " + room, "manufacturer": "TAFA",
                "model": "Device Bridge"}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, SIGNAL, self._changed))

    def _changed(self, identifier):
        if identifier == self.device_id:
            self.async_write_ha_state()

def setup_tablets(hass, entry, add_entities, factory):
    controller = hass.data[DOMAIN][KEY]
    enrolled = set()
    def add(identifier=None):
        ids = [identifier] if identifier is not None else list(controller.devices)
        new = []
        for device_id in ids:
            if device_id in controller.devices and device_id not in enrolled:
                enrolled.add(device_id)
                new.extend(factory(controller, device_id))
        if new:
            add_entities(new)
    add()
    entry.async_on_unload(async_dispatcher_connect(
        hass, REGISTERED_SIGNAL, add))
