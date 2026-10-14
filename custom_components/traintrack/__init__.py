"""TrainTrack integration for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import TrainTrackCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TrainTrack from a config entry."""
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    coordinator = TrainTrackCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload TrainTrack after its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload TrainTrack platforms."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


async def async_migrate_entry(  # NOSONAR(S7503)
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Migrate configuration entries when needed."""
    if entry.version == 1:
        data = dict(entry.data)
        data.pop("session_token", None)
        data.setdefault(CONF_API_KEY, "")
        data.setdefault(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        hass.config_entries.async_update_entry(entry, data=data, version=2)
    return entry.version <= 2
