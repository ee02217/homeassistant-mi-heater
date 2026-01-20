"""Select platform for Xiaomi miHeater integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MiHeaterData, get_miheater_data


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up miHeater select entities from a config entry."""
    data = get_miheater_data(hass, entry.entry_id)
    if data.properties.get("led_brightness") is None:
        return
    async_add_entities([MiHeaterLedBrightnessSelect(data)])


class MiHeaterLedBrightnessSelect(CoordinatorEntity, SelectEntity):
    """Representation of a LED brightness selector."""

    _attr_options = ["on", "off"]

    def __init__(self, data: MiHeaterData) -> None:
        super().__init__(data.coordinator)
        self._api = data.api
        self._model = data.model
        self._attr_name = f"{data.name} LED Brightness"
        self._attr_unique_id = f"{data.unique_id}_led_brightness" if data.unique_id else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data.unique_id or data.name)},
            manufacturer="Xiaomi",
            model=data.model,
            name=data.name,
        )
        if data.model == "zhimi.heater.za2":
            self._attr_options = ["on", "off", "dim"]

    @property
    def current_option(self) -> str | None:
        value = self.coordinator.data.get("led_brightness")
        if value is None:
            return None
        return self._normalize_led_brightness(value)

    async def async_select_option(self, option: str) -> None:
        await self._api.async_set_led_brightness(option)
        await self.coordinator.async_request_refresh()

    def _normalize_led_brightness(self, value: int | bool) -> str:
        if self._model == "zhimi.heater.za2" and value:
            value = 3 - int(value)
        return {0: "on", 1: "off", 2: "dim"}.get(int(value), "unknown")
