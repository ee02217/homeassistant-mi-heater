"""Number platform for Xiaomi miHeater integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MAX_TEMP, DEFAULT_MIN_TEMP, DOMAIN, MODEL_LIMITS
from .coordinator import MiHeaterData, get_miheater_data


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up miHeater numbers from a config entry."""
    data = get_miheater_data(hass, entry.entry_id)
    if data.properties.get("countdown_time") is None:
        return
    async_add_entities([MiHeaterDelayOffNumber(data)])


class MiHeaterDelayOffNumber(CoordinatorEntity, NumberEntity):
    """Representation of a delay-off timer."""

    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, data: MiHeaterData) -> None:
        super().__init__(data.coordinator)
        self._api = data.api
        self._attr_name = f"{data.name} Delay Off"
        self._attr_unique_id = f"{data.unique_id}_delay_off" if data.unique_id else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data.unique_id or data.name)},
            manufacturer="Xiaomi",
            model=data.model,
            name=data.name,
        )
        limits = MODEL_LIMITS.get(
            data.model,
            {"temperature_range": (DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP), "delay_off_range": (0, 12)},
        )
        min_hours, max_hours = limits.get("delay_off_range", (0, 12))
        self._attr_native_min_value = min_hours * 60
        self._attr_native_max_value = max_hours * 60

    @property
    def native_value(self) -> float | None:
        seconds = self.coordinator.data.get("delay_off")
        if seconds is None:
            return None
        return int(seconds) / 60

    async def async_set_native_value(self, value: float) -> None:
        await self._api.async_set_delay_off(int(value) * 60)
        await self.coordinator.async_request_refresh()
