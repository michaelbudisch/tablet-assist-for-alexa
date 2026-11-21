"""Setup without exposing credentials in entity state."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType
from .const import DOMAIN

def schema():
    return vol.Schema({
        vol.Optional("qwen_token"): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
    })

class JarvisTabletFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        errors = {}
        if user_input is not None:
            token = user_input.get("qwen_token", "").strip()
            if token and len(token) < 32:
                errors["qwen_token"] = "invalid_token"
            else:
                return self.async_create_entry(
                    title="Jarvis Tablet Audio",
                    data={"qwen_token": token},
                )
        return self.async_show_form(step_id="user", data_schema=schema(), errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input.get("qwen_token", "").strip()
            if token and len(token) < 32:
                errors["qwen_token"] = "invalid_token"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates={"qwen_token": token},
                )
        return self.async_show_form(step_id="reconfigure", data_schema=schema(), errors=errors)
