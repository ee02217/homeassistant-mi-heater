"""Switch platform for Xiaomi miHeater integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MiHeaterData, get_miheater_data


@dataclass(frozen=True, kw_only=True)
class MiHeaterSwitchDescription(SwitchEntityDescription):
    """Describes miHeater switch."""

    property_name: str


SWITCH_DESCRIPTIONS: tuple[MiHeaterSwitchDescription, ...] = (
    MiHeaterSwitchDescription(
        key="child_lock",
        name="Child Lock",
        property_name="child_lock",
    ),
    MiHeaterSwitchDescription(
        key="buzzer",
        name="Buzzer",
        property_name="buzzer",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up miHeater switches from a config entry."""
    data = get_miheater_data(hass, entry.entry_id)
    entities: list[MiHeaterSwitch] = []
    for description in SWITCH_DESCRIPTIONS:
        if data.properties.get(description.property_name) is None:
            continue
        entities.append(MiHeaterSwitch(data, description))
    async_add_entities(entities)


class MiHeaterSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a miHeater switch."""

    def __init__(self, data: MiHeaterData, description: MiHeaterSwitchDescription):
        super().__init__(data.coordinator)
        self.entity_description = description
        self._api = data.api
        self._attr_name = f"{data.name} {description.name}"
        self._attr_unique_id = (
            f"{data.unique_id}_{description.key}" if data.unique_id else None
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data.unique_id or data.name)},
            manufacturer="Xiaomi",
            model=data.model,
            name=data.name,
        )

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self.entity_description.property_name)

    async def async_turn_on(self, **kwargs) -> None:
        if self.entity_description.key == "child_lock":
            await self._api.async_set_child_lock(True)
        elif self.entity_description.key == "buzzer":
            await self._api.async_set_buzzer(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        if self.entity_description.key == "child_lock":
            await self._api.async_set_child_lock(False)
        elif self.entity_description.key == "buzzer":
            await self._api.async_set_buzzer(False)
        await self.coordinator.async_request_refresh()
