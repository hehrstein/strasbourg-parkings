"""Shared coordinator for Strasbourg Parkings."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import StrasbourgParkingsApiClient, StrasbourgParkingsApiError
from .const import (
    CONF_PARKINGS,
    CONF_SCAN_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class StrasbourgParkingsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch the selected Strasbourg parkings through one shared request."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator from its config entry."""
        configured_interval = _configured_value(
            entry, CONF_SCAN_INTERVAL, DEFAULT_UPDATE_INTERVAL.total_seconds() / 60
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=_update_interval(configured_interval),
            config_entry=entry,
        )
        self._client = StrasbourgParkingsApiClient(hass)
        self._parking_ids = _as_string_list(
            _configured_value(entry, CONF_PARKINGS, [])
        )

    @property
    def parking_ids(self) -> list[str]:
        """Return selected stable parking identifiers."""
        return self._parking_ids

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the public feed once and retain only selected facilities."""
        try:
            result = await self._client.async_get_parkings()
        except StrasbourgParkingsApiError as err:
            raise UpdateFailed(str(err)) from err

        return {
            "parkings": {
                parking_id: result.parkings[parking_id]
                for parking_id in self._parking_ids
                if parking_id in result.parkings
            },
            "fetched_at": result.fetched_at.isoformat(),
        }


def _configured_value(entry: ConfigEntry, key: str, default: Any) -> Any:
    """Use options before initial-entry data."""
    return entry.options.get(key, entry.data.get(key, default))


def _update_interval(value: Any) -> timedelta:
    """Return a valid update interval without exceeding the source cadence."""
    try:
        return timedelta(minutes=max(MIN_SCAN_INTERVAL_MINUTES, int(value)))
    except (TypeError, ValueError):
        return DEFAULT_UPDATE_INTERVAL


def _as_string_list(value: Any) -> list[str]:
    """Normalize a config-flow multi-select value."""
    if not isinstance(value, list):
        value = [value] if value else []
    return list(dict.fromkeys(str(item) for item in value if item))
