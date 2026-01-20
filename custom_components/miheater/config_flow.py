import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MiHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mi Heater."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        self._errors = {}

        if user_input is not None:
            valid = await self._test_connection(user_input)
            if valid:
                return self.async_create_entry(title="Mi Heater", data=user_input)
            else:
                self._errors["base"] = "cannot_connect"

        data_schema = vol.Schema({
            vol.Required("host"): str,
            vol.Required("token"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=self._errors
        )

    async def _test_connection(self, user_input):
        """Test if the provided credentials are valid."""
        # Implement connection testing logic here
        return True

from miio import Device, DeviceException

async def _test_connection(self, user_input):
    """Test if the provided credentials are valid."""
    host = user_input["host"]
    token = user_input["token"]

    try:
        device = Device(host, token)
        # Try fetching some data to verify connection
        info = await self.hass.async_add_executor_job(device.info)
        _LOGGER.debug("Device info: %s", info)
        return True
    except DeviceException as error:
        _LOGGER.error("Connection failed: %s", error)
        return False
