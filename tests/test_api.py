"""Tests for the Strasbourg Open Data API parsing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from custom_components.strasbourg_parkings.api import StrasbourgParkingsApiClient

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


class FakeResponse:
    """Minimal aiohttp response fixture."""

    def __init__(self, payload: dict[str, Any]) -> None:
        """Store a controlled Open Data response."""
        self._payload = payload

    async def __aenter__(self) -> FakeResponse:
        """Enter the async response context."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit the async response context."""

    def raise_for_status(self) -> None:
        """Simulate a successful HTTP response."""

    async def json(self) -> dict[str, Any]:
        """Return the recorded fixture data."""
        return self._payload


class FakeSession:
    """Minimal HTTP session fixture."""

    def __init__(self, payload: dict[str, Any]) -> None:
        """Store the response returned by GET."""
        self._payload = payload
        self.calls = 0

    def get(self, *args: Any, **kwargs: Any) -> FakeResponse:
        """Record one request and return the fixture response."""
        self.calls += 1
        return FakeResponse(self._payload)


async def test_client_normalizes_public_parking_response(
    hass, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The public API fields become stable Home Assistant values."""
    fixture_path = Path(__file__).parent / "fixtures" / "parkings.json"
    session = FakeSession(json.loads(fixture_path.read_text("utf-8")))
    monkeypatch.setattr(
        "custom_components.strasbourg_parkings.api.async_get_clientsession",
        lambda _hass: session,
    )

    result = await StrasbourgParkingsApiClient(hass).async_get_parkings()

    assert session.calls == 1
    assert set(result.parkings) == {"1382_DEP_8", "1400_DEP_26"}
    assert result.parkings["1382_DEP_8"] == {
        "id": "1382_DEP_8",
        "name": "Parking Gare Wodli",
        "free_spaces": 492,
        "total_capacity": 955,
        "occupancy_ratio": pytest.approx(0.4848167539267016),
        "occupancy_percentage": 48.5,
        "is_open": True,
        "status": "Ouvert",
        "status_code": 1,
        "realtime_status": "GREEN",
        "display_status": "492",
        "display_free_spaces": "490",
        "occupancy_color": "vert",
        "latitude": pytest.approx(48.5873845279566),
        "longitude": pytest.approx(7.7367710015538),
    }


def test_parser_keeps_unknown_open_state_as_none() -> None:
    """An undocumented state code must not be guessed as open or closed."""
    from custom_components.strasbourg_parkings.api import _normalize_parking

    parking = _normalize_parking(
        {"nom_parking": "Test", "idsurfs": "test", "etat": 9}
    )

    assert parking is not None
    assert parking["is_open"] is None
