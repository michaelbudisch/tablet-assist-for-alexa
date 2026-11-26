"""Remote settings switches; Home Assistant owns the saved value."""
from homeassistant.components.switch import SwitchEntity
from .tablet_entities import TabletMixin, setup_tablets

SWITCHES = {"muted": ("Mikrofon stumm", "mdi:microphone-off"),
            "screen_awake": ("Display hell", "mdi:tablet"),
            "display_control_enabled": ("Displaysteuerung aktiv", "mdi:brightness-6")}
class TabletSwitch(TabletMixin, SwitchEntity):
    def __init__(self, controller, device_id, key):
        super().__init__(controller, device_id, key, SWITCHES[key][0])
        self._attr_icon = SWITCHES[key][1]
    @property
    def is_on(self):
        return bool(self.controller.devices.get(self.device_id, {}).get(self.key, False))
    async def async_turn_on(self, **kwargs):
        await self.controller.set_value(self.device_id, self.key, True)
    async def async_turn_off(self, **kwargs):
        await self.controller.set_value(self.device_id, self.key, False)

async def async_setup_entry(hass, entry, async_add_entities):
    setup_tablets(hass, entry, async_add_entities,
                  lambda controller, device: [TabletSwitch(controller, device, key) for key in SWITCHES])
