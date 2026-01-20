"""Climate platform for Xiaomi miHeater integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from miio import Device, DeviceException

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVAC_MODE_HEAT, HVAC_MODE_OFF
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, CONF_TOKEN, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_MODEL, DOMAIN, MAX_TEMP, MIN_TEMP

_LOGGER = logging.getLogger(__name__)

MODEL_PROPERTIES = {
    "zhimi.heater.mc2": {
        "power": (2, 1),
        "target_temperature": (2, 5),
        "current_temperature": (4, 7),
        "humidity": None,
    },
    "zhimi.heater.zb1": {
        "power": (2, 2),
        "target_temperature": (2, 6),
        "current_temperature": (5, 8),
        "humidity": (5, 7),
    },
    "zhimi.heater.za2": {
        "power": (2, 2),
        "target_temperature": (2, 6),
        "current_temperature": (5, 8),
        "humidity": (5, 7),
    },
}


class MiHeaterApi:
    """API wrapper for miHeater."""

    def __init__(self, hass: HomeAssistant, host: str, token: str, model: str) -> None:
        self._hass = hass
        self._device = Device(host, token)
        self._model = model

    async def _async_raw_command(self, method: str, params: list[dict]) -> list[dict]:
        def _raw() -> list[dict]:
            return self._device.raw_command(method, params)

        return await self._hass.async_add_executor_job(_raw)

    async def async_get_status(self) -> dict:
        """Fetch device status."""
        if self._model not in MODEL_PROPERTIES:
            raise UpdateFailed(f"Unsupported model: {self._model}")

        props = MODEL_PROPERTIES[self._model]
        data: dict[str, int | float | bool] = {}

        try:
            power = await self._async_raw_command(
                "get_properties",
                [{"siid": props["power"][0], "piid": props["power"][1]}],
            )
            target = await self._async_raw_command(
                "get_properties",
                [
                    {
                        "siid": props["target_temperature"][0],
                        "piid": props["target_temperature"][1],
                    }
                ],
            )
            current = await self._async_raw_command(
                "get_properties",
                [
                    {
                        "siid": props["current_temperature"][0],
                        "piid": props["current_temperature"][1],
                    }
                ],
            )
            humidity_value = 0
            if props["humidity"] is not None:
                humidity = await self._async_raw_command(
                    "get_properties",
                    [
                        {
                            "siid": props["humidity"][0],
                            "piid": props["humidity"][1],
                        }
                    ],
                )
                humidity_value = humidity[0]["value"]

            data["power"] = power[0]["value"]
            data["target_temperature"] = target[0]["value"]
            data["current_temperature"] = current[0]["value"]
            data["humidity"] = humidity_value
        except DeviceException as err:
            raise UpdateFailed(f"Failed to fetch heater data: {err}") from err

        return data

    async def async_set_temperature(self, temperature: int) -> None:
        """Set target temperature."""
        props = MODEL_PROPERTIES[self._model]
        await self._async_raw_command(
            "set_properties",
            [
                {
                    "value": int(temperature),
                    "siid": props["target_temperature"][0],
                    "piid": props["target_temperature"][1],
                }
            ],
        )

    async def async_set_power(self, on: bool) -> None:
        """Turn device on or off."""
        props = MODEL_PROPERTIES[self._model]
        await self._async_raw_command(
            "set_properties",
            [
                {
                    "value": bool(on),
                    "siid": props["power"][0],
                    "piid": props["power"][1],
                }
            ],
        )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up miHeater climate entities from config entry."""
    host = entry.data[CONF_HOST]
    token = entry.data[CONF_TOKEN]
    model = entry.data[CONF_MODEL]
    name = entry.data[CONF_NAME]

    if model not in MODEL_PROPERTIES:
        _LOGGER.error("Unsupported miHeater model: %s", model)
        raise ConfigEntryNotReady

    api = MiHeaterApi(hass, host, token, model)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=api.async_get_status,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([MiHeaterEntity(name, api, coordinator, entry.unique_id)])


class MiHeaterEntity(CoordinatorEntity, ClimateEntity):
    """Representation of a Xiaomi Heater as a climate entity."""

    _attr_temperature_unit = TEMP_CELSIUS
    _attr_hvac_modes = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = 1

    def __init__(
        self,
        name: str,
        api: MiHeaterApi,
        coordinator: DataUpdateCoordinator,
        unique_id: str | None,
    ) -> None:
        self._api = api
        self._attr_name = name
        self._attr_unique_id = unique_id
        super().__init__(coordinator)

    @property
    def hvac_mode(self) -> str:
        return HVAC_MODE_HEAT if self.coordinator.data["power"] else HVAC_MODE_OFF

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data["target_temperature"]

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data["current_temperature"]

    @property
    def current_humidity(self) -> int | None:
        return self.coordinator.data["humidity"]

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self._api.async_set_temperature(int(temperature))
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        if hvac_mode == HVAC_MODE_HEAT:
            await self._api.async_set_power(True)
        elif hvac_mode == HVAC_MODE_OFF:
            await self._api.async_set_power(False)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "humidity": self.coordinator.data["humidity"],
        }
