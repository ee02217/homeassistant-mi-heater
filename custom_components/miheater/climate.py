"""Climate platform for Xiaomi miHeater integration."""

from __future__ import annotations

from datetime import timedelta
import logging

import voluptuous as vol
from miio import Device, DeviceException

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_platform
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_MODEL,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DOMAIN,
    MODEL_LIMITS,
    MODEL_PROPERTIES,
)

_LOGGER = logging.getLogger(__name__)


class MiHeaterApi:
    """API wrapper for miHeater."""

    def __init__(self, hass: HomeAssistant, host: str, token: str, model: str) -> None:
        self._hass = hass
        self._device = Device(host, token)
        self._model = model
        self._properties = MODEL_PROPERTIES[model]

    async def _async_raw_command(self, method: str, params: list[dict]) -> list[dict]:
        def _raw() -> list[dict]:
            return self._device.raw_command(method, params)

        return await self._hass.async_add_executor_job(_raw)

    async def async_get_status(self) -> dict:
        """Fetch device status."""
        if self._model not in MODEL_PROPERTIES:
            raise UpdateFailed(f"Unsupported model: {self._model}")

        data: dict[str, int | float | bool | None] = {}
        property_map = self._build_property_map()
        requested = [
            {"siid": siid, "piid": piid} for (siid, piid) in property_map.values()
        ]

        try:
            values = await self._async_raw_command("get_properties", requested)
        except DeviceException as err:
            raise UpdateFailed(f"Failed to fetch heater data: {err}") from err

        values_by_key = {
            (value["siid"], value["piid"]): value.get("value")
            for value in values
            if value.get("code") == 0
        }
        for key, (siid, piid) in property_map.items():
            data[key] = values_by_key.get((siid, piid))

        if data.get("countdown_time") is not None:
            data["delay_off"] = int(data["countdown_time"]) * 3600
        else:
            data["delay_off"] = None

        return data

    async def async_set_temperature(self, temperature: int) -> None:
        """Set target temperature."""
        await self._async_set_property("target_temperature", int(temperature))

    async def async_set_power(self, on: bool) -> None:
        """Turn device on or off."""
        await self._async_set_property("power", bool(on))

    async def async_set_child_lock(self, enabled: bool) -> None:
        """Set child lock."""
        await self._async_set_property("child_lock", bool(enabled))

    async def async_set_buzzer(self, enabled: bool) -> None:
        """Set buzzer."""
        await self._async_set_property("buzzer", bool(enabled))

    async def async_set_led_brightness(self, brightness: str) -> None:
        """Set LED brightness."""
        mapped = {"on": 0, "off": 1, "dim": 2}[brightness]
        if self._model == "zhimi.heater.za2" and mapped:
            mapped = 3 - mapped
        await self._async_set_property("led_brightness", mapped)

    async def async_set_delay_off(self, seconds: int) -> None:
        """Set delay off in seconds."""
        hours = int(seconds // 3600)
        await self._async_set_property("countdown_time", hours)

    def _build_property_map(self) -> dict[str, tuple[int, int]]:
        return {
            key: value
            for key, value in self._properties.items()
            if value is not None
        }

    async def _async_set_property(self, name: str, value: int | bool) -> None:
        prop = self._properties.get(name)
        if prop is None:
            raise UpdateFailed(f"Property {name} is not supported by {self._model}")
        await self._async_raw_command(
            "set_properties",
            [{"value": value, "siid": prop[0], "piid": prop[1]}],
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

    async_add_entities(
        [MiHeaterEntity(name, model, api, coordinator, entry.unique_id)]
    )


class MiHeaterEntity(CoordinatorEntity, ClimateEntity):
    """Representation of a Xiaomi Heater as a climate entity."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = 1

    def __init__(
        self,
        name: str,
        model: str,
        api: MiHeaterApi,
        coordinator: DataUpdateCoordinator,
        unique_id: str | None,
    ) -> None:
        self._api = api
        self._attr_name = name
        limits = MODEL_LIMITS.get(
            model,
            {"temperature_range": (DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP)},
        )
        min_temp, max_temp = limits["temperature_range"]
        self._attr_min_temp = min_temp
        self._attr_max_temp = max_temp
        self._limits = limits
        self._model = model
        self._properties = MODEL_PROPERTIES[model]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id or name)},
            manufacturer="Xiaomi",
            model=model,
            name=name,
        )
        self._attr_unique_id = unique_id
        super().__init__(coordinator)

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
