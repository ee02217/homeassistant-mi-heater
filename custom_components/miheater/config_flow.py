"""Config flow for Xiaomi miHeater integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from miio import Device, DeviceException

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant

from .const import CONF_MODEL, DEFAULT_NAME, DOMAIN, MODEL_PROPERTIES

AUTO_MODEL = "auto"

_LOGGER = logging.getLogger(__name__)


async def _async_get_device_info(
    hass: HomeAssistant, host: str, token: str
) -> tuple[str, str]:
    """Fetch model and mac address from the device."""
    def _get_info() -> tuple[str, str]:
        device = Device(host, token)
        info = device.info()
        return info.model, info.mac_address

    return await hass.async_add_executor_job(_get_info)


class MiHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xiaomi miHeater."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        model_options = [AUTO_MODEL, *MODEL_PROPERTIES.keys()]
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_TOKEN): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(CONF_MODEL, default=AUTO_MODEL): vol.In(model_options),
            }
        )

        if user_input is not None:
            host = user_input[CONF_HOST]
            token = user_input[CONF_TOKEN]
            name = user_input.get(CONF_NAME, DEFAULT_NAME)
            model = user_input.get(CONF_MODEL)

            try:
                detected_model, mac = await _async_get_device_info(
                    self.hass, host, token
                )
            except DeviceException as err:
                _LOGGER.warning("Unable to connect to miHeater: %s", err)
                errors["base"] = "cannot_connect"
            else:
                if not model or model == AUTO_MODEL:
                    model = detected_model

                if model not in MODEL_PROPERTIES:
                    errors["base"] = "unsupported_model"
                    return self.async_show_form(
                        step_id="user", data_schema=data_schema, errors=errors
                    )

                unique_id = f"{model}-{mac}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: host,
                        CONF_TOKEN: token,
                        CONF_NAME: name,
                        CONF_MODEL: model,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
