from homeassistant import config_entries
from .const import DOMAIN
class JarvisAndroidConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        return self.async_create_entry(title="Jarvis Speech Router", data={})
