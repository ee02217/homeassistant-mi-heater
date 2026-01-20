"""Xiaomi miHeater integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN

from .const import CONF_MODEL, DEFAULT_NAME, DOMAIN, MODEL_PROPERTIES
from .coordinator import MiHeaterApi, MiHeaterData

PLATFORMS: list[str] = ["climate", "number", "select", "sensor", "switch"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the miHeater integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up miHeater from a config entry."""
    model = entry.data[CONF_MODEL]
    if model not in MODEL_PROPERTIES:
        raise ConfigEntryNotReady

    api = MiHeaterApi(hass, entry.data[CONF_HOST], entry.data[CONF_TOKEN], model)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=api.async_get_status,
        update_interval=timedelta(seconds=30),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MiHeaterData(
        api=api,
        coordinator=coordinator,
        model=model,
        name=entry.data.get(CONF_NAME, DEFAULT_NAME),
        unique_id=entry.unique_id,
        properties=MODEL_PROPERTIES[model],
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
