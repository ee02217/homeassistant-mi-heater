"""Platform for climate integration of Mi Heater."""

import logging
from datetime import timedelta

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Import the device library
from miio import DeviceException
from miio.heater import MiHeater

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Mi Heater climate device based on a config entry."""
    host = entry.data.get("host")
    token = entry.data.get("token")
    name = "Mi Heater"

    # Initialize the device
    device = MiHeater(host, token)

    # Create a DataUpdateCoordinator to manage data updates
    coordinator = MiHeaterDataUpdateCoordinator(hass, device)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Create and add the entity
    async_add_entities([MiHeaterClimate(coordinator, name, entry.entry_id)], True)

class MiHeaterDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Mi Heater device."""

    def __init__(self, hass: HomeAssistant, device: MiHeater):
        """Initialize the coordinator."""
        self.device = device
        super().__init__(
            hass,
            _LOGGER,
            name="Mi Heater Data Update",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from the device."""
        try:
            data = await self.hass.async_add_executor_job(self.device.status)
            return data
        except DeviceException as error:
            raise UpdateFailed(f"Error fetching data: {error}") from error

class MiHeaterClimate(ClimateEntity):
    """Representation of the Mi Heater climate device."""

    def __init__(self, coordinator: MiHeaterDataUpdateCoordinator, name: str, entry_id: str):
        """Initialize the climate device."""
        self.coordinator = coordinator
        self._name = name
        self._unique_id = entry_id
        self._supported_features = SUPPORT_TARGET_TEMPERATURE
        self._hvac_modes = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
        self._attr_temperature_unit = TEMP_CELSIUS

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the climate device."""
        return self._unique_id

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return self._hvac_modes

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        if self.coordinator.data.is_on:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.coordinator.data.temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.coordinator.data.target_temperature

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 16  # Adjust based on device capabilities

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 32  # Adjust based on device capabilities

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.hass.async_add_executor_job(
                self.coordinator.device.set_target_temperature, temperature
            )
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target HVAC mode."""
        if hvac_mode == HVAC_MODE_HEAT:
            await self.hass.async_add_executor_job(self.coordinator.device.on)
        elif hvac_mode == HVAC_MODE_OFF:
            await self.hass.async_add_executor_job(self.coordinator.device.off)
        else:
            _LOGGER.error("Unsupported HVAC mode: %s", hvac_mode)
            return
        await self.coordinator.async_request_refresh()

    async def async_update(self):
        """Fetch new state data for the entity."""
        await self.coordinator.async_request_refresh()
