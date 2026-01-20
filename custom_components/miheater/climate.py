"""Climate platform for Xiaomi miHeater integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed

from .const import DEFAULT_MAX_TEMP, DEFAULT_MIN_TEMP, DOMAIN, MODEL_LIMITS
from .coordinator import MiHeaterData, get_miheater_data


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up miHeater climate entities from config entry."""
    data = get_miheater_data(hass, entry.entry_id)

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "set_child_lock",
        {"lock": cv.boolean},
        "async_set_child_lock",
        required_features=None,
    )
    platform.async_register_entity_service(
        "set_buzzer",
        {"enabled": cv.boolean},
        "async_set_buzzer",
        required_features=None,
    )
    platform.async_register_entity_service(
        "set_led_brightness",
        {"brightness": vol.In(["on", "off", "dim"])},
        "async_set_led_brightness",
        required_features=None,
    )
    platform.async_register_entity_service(
        "set_delay_off",
        {"seconds": vol.Coerce(int)},
        "async_set_delay_off",
        required_features=None,
    )

    async_add_entities([MiHeaterEntity(data)])


class MiHeaterEntity(CoordinatorEntity, ClimateEntity):
    """Representation of a Xiaomi Heater as a climate entity."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = 1

    def __init__(
        self,
        data: MiHeaterData,
    ) -> None:
        self._api = data.api
        self._attr_name = data.name
        limits = MODEL_LIMITS.get(
            data.model,
            {"temperature_range": (DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP)},
        )
        min_temp, max_temp = limits["temperature_range"]
        self._attr_min_temp = min_temp
        self._attr_max_temp = max_temp
        self._limits = limits
        self._model = data.model
        self._properties = data.properties
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data.unique_id or data.name)},
            manufacturer="Xiaomi",
            model=data.model,
            name=data.name,
        )
        self._attr_unique_id = data.unique_id
        super().__init__(data.coordinator)

    @property
    def hvac_mode(self) -> str:
        return HVACMode.HEAT if self.coordinator.data["power"] else HVACMode.OFF

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data["target_temperature"]

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data["current_temperature"]

    @property
    def extra_state_attributes(self) -> dict[str, int | float | bool | None]:
        data = self.coordinator.data
        attributes: dict[str, int | float | bool | None] = {}
        humidity = data.get("humidity")
        if humidity is not None:
            attributes["humidity"] = humidity
        child_lock = data.get("child_lock")
        if child_lock is not None:
            attributes["child_lock"] = child_lock
        buzzer = data.get("buzzer")
        if buzzer is not None:
            attributes["buzzer"] = buzzer
        led_brightness = data.get("led_brightness")
        if led_brightness is not None:
            attributes["led_brightness"] = self._normalize_led_brightness(
                led_brightness
            )
        delay_off = data.get("delay_off")
        if delay_off is not None:
            attributes["delay_off_seconds"] = delay_off
        return attributes

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self._api.async_set_temperature(int(temperature))
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        if hvac_mode == HVACMode.HEAT:
            await self._api.async_set_power(True)
        elif hvac_mode == HVACMode.OFF:
            await self._api.async_set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_set_child_lock(self, lock: bool) -> None:
        if self._properties.get("child_lock") is None:
            raise UpdateFailed("Child lock is not supported by this model")
        await self._api.async_set_child_lock(lock)
        await self.coordinator.async_request_refresh()

    async def async_set_buzzer(self, enabled: bool) -> None:
        if self._properties.get("buzzer") is None:
            raise UpdateFailed("Buzzer is not supported by this model")
        await self._api.async_set_buzzer(enabled)
        await self.coordinator.async_request_refresh()

    async def async_set_led_brightness(self, brightness: str) -> None:
        if self._properties.get("led_brightness") is None:
            raise UpdateFailed("LED brightness is not supported by this model")
        if brightness == "dim" and self._model != "zhimi.heater.za2":
            raise UpdateFailed("Dim brightness is not supported by this model")
        await self._api.async_set_led_brightness(brightness)
        await self.coordinator.async_request_refresh()

    async def async_set_delay_off(self, seconds: int) -> None:
        if self._properties.get("countdown_time") is None:
            raise UpdateFailed("Delay off is not supported by this model")
        min_hours, max_hours = self._limits.get("delay_off_range", (0, 12))
        min_seconds, max_seconds = min_hours * 3600, max_hours * 3600
        if seconds < min_seconds or seconds > max_seconds:
            raise UpdateFailed(
                f"Delay off must be between {min_seconds} and {max_seconds} seconds"
            )
        await self._api.async_set_delay_off(seconds)
        await self.coordinator.async_request_refresh()

    def _normalize_led_brightness(self, value: int | bool) -> str:
        if self._model == "zhimi.heater.za2" and value:
            value = 3 - int(value)
        return {0: "on", 1: "off", 2: "dim"}.get(int(value), "unknown")
