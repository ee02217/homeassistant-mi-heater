"""Coordinator and API for Xiaomi miHeater integration."""

from __future__ import annotations

from dataclasses import dataclass

from miio import Device, DeviceException

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MODEL_PROPERTIES


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


@dataclass(slots=True)
class MiHeaterData:
    """Shared data for miHeater entities."""

    api: MiHeaterApi
    coordinator: DataUpdateCoordinator
    model: str
    name: str
    unique_id: str | None
    properties: dict[str, tuple[int, int] | None]


def get_miheater_data(hass: HomeAssistant, entry_id: str) -> MiHeaterData:
    """Fetch stored miHeater data."""
    data = hass.data.get(DOMAIN, {}).get(entry_id)
    if data is None:
        raise ConfigEntryNotReady
    return data
