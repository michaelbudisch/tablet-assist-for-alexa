"""Select the wake word per tablet from HA."""
from homeassistant.components.select import SelectEntity
from .tablet_entities import TabletMixin, setup_tablets

OPTIONS = ["Hey Jarvis", "Jarvis", "Alexa", "Alle drei"]
class TabletWakeword(TabletMixin, SelectEntity):
    def __init__(self, controller, device_id):
        super().__init__(controller, device_id, "word", "Rufwort")
        self._attr_options = OPTIONS
        self._attr_icon = "mdi:microphone-message"
    @property
    def current_option(self):
        return self.controller.devices.get(self.device_id, {}).get("word", OPTIONS[0])
    async def async_select_option(self, option):
        await self.controller.set_value(self.device_id, "word", option)

async def async_setup_entry(hass, entry, async_add_entities):
    setup_tablets(hass, entry, async_add_entities,
                  lambda controller, device: [TabletWakeword(controller, device)])
