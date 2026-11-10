"""Tests for the shared Strasbourg Parkings coordinator."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.util import dt as dt_util

from custom_components.strasbourg_parkings import coordinator as coordinator_module
from custom_components.strasbourg_parkings.api import StrasbourgParkingsResult
from custom_components.strasbourg_parkings.const import (
    CONF_PARKINGS,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


class FakeParkingApiClient:
    """Parking API client returning a deterministic result."""

    async def async_get_parkings(self) -> StrasbourgParkingsResult:
        """Return two source records through one shared call."""
        return StrasbourgParkingsResult(
            {
                "first": {"id": "first", "name": "First", "free_spaces": 12},
                "second": {"id": "second", "name": "Second", "free_spaces": 4},
            },
            dt_util.utcnow(),
        )


def make_entry(parking_ids: list[str], interval: int = 3) -> MockConfigEntry:
    """Create a Strasbourg Parkings config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="test-entry",
        data={CONF_PARKINGS: parking_ids, CONF_SCAN_INTERVAL: interval},
    )


async def test_coordinator_keeps_only_selected_parkings(
    hass, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A single source request feeds only the selected Home Assistant devices."""
    monkeypatch.setattr(
        coordinator_module, "StrasbourgParkingsApiClient", lambda _hass: FakeParkingApiClient()
    )
    coordinator = coordinator_module.StrasbourgParkingsCoordinator(
        hass, make_entry(["second", "missing"])
    )

    data = await coordinator._async_update_data()

    assert data["parkings"] == {
        "second": {"id": "second", "name": "Second", "free_spaces": 4}
    }
    assert data["fetched_at"]


async def test_coordinator_enforces_source_refresh_floor(hass) -> None:
    """Even an invalid legacy setting cannot poll faster than three minutes."""
    coordinator = coordinator_module.StrasbourgParkingsCoordinator(
        hass, make_entry(["first"], interval=1)
    )

    assert coordinator.update_interval == timedelta(minutes=3)
