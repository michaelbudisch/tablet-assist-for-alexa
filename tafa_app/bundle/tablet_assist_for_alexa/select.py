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

class TabletMicMode(TabletMixin, SelectEntity):
    """Choose native voice triggering; muted remains an independent switch."""
    _mapping = {"Rufwort": "wake", "Immer an": "continuous"}
    def __init__(self, controller, device_id):
        super().__init__(controller, device_id, "voice_mode", "Nativer Sprachmodus")
        self._attr_options = list(self._mapping)
        self._attr_icon = "mdi:microphone"
    @property
    def current_option(self):
        mode = self.controller.devices.get(self.device_id, {}).get("voice_mode", "wake")
        return next((name for name, value in self._mapping.items() if value == mode), "Rufwort")
    async def async_select_option(self, option):
        if option not in self._mapping:
            raise ValueError("Unknown microphone mode")
        await self.controller.set_value(self.device_id, "voice_mode", self._mapping[option])

class TabletFollowupLimit(TabletMixin, SelectEntity):
    """Additional native questions without wakeword, configured per tablet."""
    _mapping = {"App-Einstellung": -1, "Aus": 0, "1": 1, "2": 2,
                "3": 3, "5": 5, "10": 10, "20": 20, "50": 50, "100": 100}

    def __init__(self, controller, device_id):
        super().__init__(controller, device_id, "followup_limit", "Anschlussfragen (HA-Grenze)")
        self._attr_icon = "mdi:comment-multiple-outline"
        saved = controller.devices.get(device_id, {}).get("followup_limit", -1)
        self._attr_options = list(self._mapping)
        if isinstance(saved, int) and 0 <= saved <= 100 and str(saved) not in self._attr_options:
            self._attr_options.append(str(saved))

    @property
    def current_option(self):
        value = self.controller.devices.get(self.device_id, {}).get("followup_limit", -1)
        return "App-Einstellung" if value == -1 else str(value)

    async def async_select_option(self, option):
        if option not in self._attr_options:
            raise ValueError("Unknown follow-up limit")
        value = self._mapping.get(option)
        if value is None:
            value = int(option)
        await self.controller.set_value(self.device_id, "followup_limit", value)


async def async_setup_entry(hass, entry, async_add_entities):
    setup_tablets(hass, entry, async_add_entities,
                  lambda controller, device: [TabletWakeword(controller, device), TabletMicMode(controller, device), TabletFollowupLimit(controller, device)])
