"""Legacy tablet audio configuration; GPU services run on trusted LAN."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig
from .const import DOMAIN


def schema():
    # API-key entry is intentionally removed; the worker is local-network only.
    return vol.Schema({})


class JarvisTabletFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return VisionOptions()

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if user_input is not None:
            return self.async_create_entry(title="Jarvis Tablet Audio", data={})
        return self.async_show_form(step_id="user", data_schema=schema())

    async def async_step_reconfigure(self, user_input=None):
        if user_input is not None:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(), data_updates={}
            )
        return self.async_show_form(step_id="reconfigure", data_schema=schema())


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
