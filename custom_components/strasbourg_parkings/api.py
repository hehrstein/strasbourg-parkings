"""Client for the Eurometropole de Strasbourg parking dataset."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import API_URL

_LOGGER = logging.getLogger(__name__)


class StrasbourgParkingsApiError(Exception):
    """Raised when the Strasbourg Open Data parking feed cannot be used."""


@dataclass(frozen=True, slots=True)
class StrasbourgParkingsResult:
    """Normalized response and the time it was retrieved."""

    parkings: dict[str, dict[str, Any]]
    fetched_at: datetime


class StrasbourgParkingsApiClient:
    """Read the public real-time municipal parking feed."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the client with Home Assistant's shared session."""
        self._session = async_get_clientsession(hass)

    async def async_get_parkings(self) -> StrasbourgParkingsResult:
        """Return every parking indexed by its stable Open Data identifier."""
        try:
            async with async_timeout.timeout(15):
                async with self._session.get(API_URL) as response:
                    response.raise_for_status()
                    payload = await response.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise StrasbourgParkingsApiError(
                "Unable to retrieve Strasbourg parking data"
            ) from err

        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise StrasbourgParkingsApiError("Unexpected Strasbourg parking response")

        parkings: dict[str, dict[str, Any]] = {}
        for record in results:
            parking = _normalize_parking(record)
            if parking is not None:
                parkings[parking["id"]] = parking

        if not parkings:
            raise StrasbourgParkingsApiError("No parking records in Strasbourg response")

        return StrasbourgParkingsResult(parkings, dt_util.utcnow())


def _normalize_parking(record: Any) -> dict[str, Any] | None:
    """Normalize one OpenDataSoft record without inventing unavailable values."""
    if not isinstance(record, dict):
        return None

    name = record.get("nom_parking")
    identifier = record.get("idsurfs") or record.get("ident")
    if not isinstance(name, str) or not name or identifier is None:
        _LOGGER.debug("Skipping incomplete Strasbourg parking record: %s", record)
        return None

    total = _as_int(record.get("total"))
    free = _as_int(record.get("libre"))
    rate = _as_float(record.get("taux_occup"))
    if rate is None and total and free is not None:
        rate = (total - free) / total

    position = record.get("position")
    latitude = _as_float(position.get("lat")) if isinstance(position, dict) else None
    longitude = _as_float(position.get("lon")) if isinstance(position, dict) else None
    state = _as_int(record.get("etat"))

    return {
        "id": str(identifier),
        "name": name,
        "free_spaces": free,
        "total_capacity": total,
        "occupancy_ratio": rate,
        "occupancy_percentage": round(rate * 100, 1) if rate is not None else None,
        "is_open": state == 1 if state in {0, 1, 2} else None,
        "status": record.get("etat_descriptif"),
        "status_code": state,
        "realtime_status": record.get("realtimestatus"),
        "display_status": record.get("infoappli"),
        "display_free_spaces": record.get("infousager"),
        "occupancy_color": record.get("couleur_occup"),
        "latitude": latitude,
        "longitude": longitude,
    }


def _as_int(value: Any) -> int | None:
    """Convert a source field to integer when it is genuinely numeric."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    """Convert a source field to float when it is genuinely numeric."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
