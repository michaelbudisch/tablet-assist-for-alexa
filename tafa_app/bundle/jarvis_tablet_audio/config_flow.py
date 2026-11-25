"""Setup without exposing credentials in entity state."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType, EntitySelector, EntitySelectorConfig
from .const import DOMAIN

def schema():
    return vol.Schema({
        vol.Optional("qwen_token"): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
    })

class JarvisTabletFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return VisionOptions()

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

class VisionOptions(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            from types import SimpleNamespace
            from .relay_vision import worker_url
            try:
                worker_url(SimpleNamespace(options=user_input))
            except Exception:
                errors["vision_url"] = "invalid_url"
            else:
                # Preserve options not owned by this form.
                owned = {"vision_url", "vision_outside_camera", "vision_door_camera"}
                return self.async_create_entry(title="", data={**{k: v for k, v in self.config_entry.options.items() if k not in owned}, **user_input})
        options = self.config_entry.options
        fields = {
            vol.Optional("vision_url", default=options.get("vision_url", "")): str,
        }
        for key in ("vision_outside_camera", "vision_door_camera"):
            field = vol.Optional(key, default=options[key]) if options.get(key) else vol.Optional(key)
            fields[field] = EntitySelector(EntitySelectorConfig(domain="camera"))
        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields), errors=errors)
