"""Sensor platform for Xiaomi miHeater integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MiHeaterData, get_miheater_data


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up miHeater sensors from a config entry."""
    data = get_miheater_data(hass, entry.entry_id)
    if data.properties.get("humidity") is None:
        return
    async_add_entities([MiHeaterHumiditySensor(data)])


class MiHeaterHumiditySensor(CoordinatorEntity, SensorEntity):
    """Representation of the humidity sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, data: MiHeaterData) -> None:
        super().__init__(data.coordinator)
        self._attr_name = f"{data.name} Humidity"
        self._attr_unique_id = f"{data.unique_id}_humidity" if data.unique_id else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data.unique_id or data.name)},
            manufacturer="Xiaomi",
            model=data.model,
            name=data.name,
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("humidity")
