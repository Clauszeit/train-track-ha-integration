"""Coordinator for TrainTrack connection data."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    TrainTrackApi,
    TrainTrackAuthError,
    TrainTrackConnectionError,
)
from .const import CONF_API_KEY, CONF_BASE_URL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN


class TrainTrackCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Fetch monitored connections at a steady interval."""

    def __init__(self, hass: HomeAssistant, entry: Any, api: TrainTrackApi | None = None) -> None:
        self.api = api or TrainTrackApi(
            async_get_clientsession(hass),
            entry.data[CONF_BASE_URL],
            entry.data[CONF_API_KEY],
        )
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(
                    CONF_SCAN_INTERVAL,
                    entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                )
            ),
            config_entry=entry,
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch the latest connection data."""
        try:
            return await self.api.async_get_connections()
        except TrainTrackAuthError as err:
            raise ConfigEntryAuthFailed from err
        except TrainTrackConnectionError as err:
            raise UpdateFailed("Unable to update data from TrainTrack") from err
        except HomeAssistantError as err:
            raise UpdateFailed("Unable to update data from TrainTrack") from err
