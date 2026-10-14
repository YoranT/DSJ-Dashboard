"""UI installation and appearance options (Home Assistant 2026.10)."""
import re
import probatio as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DEFAULTS, DOMAIN


def schema(values):
    return vol.Schema({
        vol.Required("theme", default=values.get("theme", "")): str,
        vol.Required("accent", default=values.get("accent", DEFAULTS["accent"])): str,
        vol.Required("original_cards", default=values.get("original_cards", True)): bool,
    })


class DSJConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="De Slimme Jongens", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DSJOptionsFlow()


class DSJOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            if re.fullmatch(r"#[0-9a-fA-F]{6}", user_input["accent"]):
                return self.async_create_entry(title="", data=user_input)
            errors["accent"] = "invalid_color"
        return self.async_show_form(
            step_id="init", data_schema=schema(user_input or self.config_entry.options),
            errors=errors,
        )
