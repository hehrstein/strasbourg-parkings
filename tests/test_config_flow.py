"""Tests for Strasbourg Parkings configuration flows."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.data_entry_flow import FlowResultType

from custom_components.strasbourg_parkings import config_flow
from custom_components.strasbourg_parkings.api import StrasbourgParkingsApiError
from custom_components.strasbourg_parkings.const import (
    CONF_PARKINGS,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_options_flow_renders_when_source_is_unavailable(
    hass, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An outage must show cannot_connect instead of raising AttributeError."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PARKINGS: ["1382_DEP_8"], CONF_SCAN_INTERVAL: 3},
    )
    entry.add_to_hass(hass)

    async def raise_api_error(_hass: Any) -> list[dict[str, str]]:
        """Simulate an unavailable municipal portal."""
        raise StrasbourgParkingsApiError("Open Data unavailable")

    monkeypatch.setattr(config_flow, "_async_load_choices", raise_api_error)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_select_step_requires_at_least_one_parking(hass) -> None:
    """The integration cannot create an empty config entry."""
    async def fake_load_choices(_hass: Any) -> list[dict[str, str]]:
        """Return one parking without calling the real public endpoint."""
        return [{"value": "1382_DEP_8", "label": "Gare Wodli"}]

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(config_flow, "_async_load_choices", fake_load_choices)
    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_flow.config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "select"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PARKINGS: [], CONF_SCAN_INTERVAL: 3}
        )
    finally:
        monkeypatch.undo()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "select_parking"}
