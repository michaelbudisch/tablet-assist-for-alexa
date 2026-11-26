"""Native microphone and display settings, one set per tablet."""
from homeassistant.components.number import NumberEntity
from .tablet_entities import TabletMixin, setup_tablets

NUMBERS = {
    "strict": ("Rufwort-Bestätigung", 1, 3, 1),
    "cooldown": ("Rufwort-Sperrzeit (s)", 3, 30, 1),
    "hold": ("Rufwort-Haltezeit (s)", 10, 90, 1),
    "pause_ms": ("Sprechpause (ms)", 900, 3200, 100),
    "mic_gain": ("Mikrofon-Verstärkung (%)", 50, 200, 10),
    "brightness": ("Displayhelligkeit (%)", 1, 100, 1),
}
class TabletNumber(TabletMixin, NumberEntity):
    def __init__(self, controller, device_id, key):
        super().__init__(controller, device_id, key, NUMBERS[key][0])
        _, minimum, maximum, step = NUMBERS[key]
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_mode = "slider"
    @property
    def native_value(self):
        return self.controller.devices.get(self.device_id, {}).get(self.key)
    async def async_set_native_value(self, value):
        await self.controller.set_value(self.device_id, self.key, int(value))

async def async_setup_entry(hass, entry, async_add_entities):
    setup_tablets(hass, entry, async_add_entities,
                  lambda controller, device: [TabletNumber(controller, device, key) for key in NUMBERS])
