"""Configuration flow for Strasbourg Parkings."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .api import StrasbourgParkingsApiClient, StrasbourgParkingsApiError
from .const import (
    CONF_PARKINGS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
    NAME,
)


class StrasbourgParkingsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Strasbourg Parkings setup."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize choices used by the select step."""
        self._parking_options: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Load the live facility list before creating the entry."""
        errors: dict[str, str] = {}
        try:
            self._parking_options = await _async_load_choices(self.hass)
        except StrasbourgParkingsApiError:
            errors["base"] = "cannot_connect"
        else:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return await self.async_step_select()

        # This deliberate empty form provides a Retry action without asking the
        # user for data that the public Open Data API already supplies.
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({}), errors=errors
        )

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user choose the municipal car parks to follow."""
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = _as_string_list(user_input.get(CONF_PARKINGS))
            if not selected:
                errors["base"] = "select_parking"
            else:
                return self.async_create_entry(
                    title=NAME,
                    data={
                        CONF_PARKINGS: selected,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

        return self.async_show_form(
            step_id="select",
            data_schema=_selection_schema(self._parking_options),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> StrasbourgParkingsOptionsFlow:
        """Return the options flow supplied with the existing config entry."""
        return StrasbourgParkingsOptionsFlow()


class StrasbourgParkingsOptionsFlow(config_entries.OptionsFlow):
    """Handle parking selection and refresh interval changes."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show current settings and keep the error form safe during an outage."""
        errors: dict[str, str] = {}
        if not hasattr(self, "_parking_options"):
            self._parking_options: list[dict[str, str]] = []
            try:
                self._parking_options = await _async_load_choices(self.hass)
            except StrasbourgParkingsApiError:
                errors["base"] = "cannot_connect"

        if user_input is not None and not errors:
            selected = _as_string_list(user_input.get(CONF_PARKINGS))
            if selected:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_PARKINGS: selected,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )
            errors["base"] = "select_parking"

        current_parkings = _as_string_list(
            self.config_entry.options.get(
                CONF_PARKINGS, self.config_entry.data.get(CONF_PARKINGS, [])
            )
        )
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
            ),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=_selection_schema(
                self._parking_options, current_parkings, current_interval
            ),
            errors=errors,
        )


async def _async_load_choices(hass: HomeAssistant) -> list[dict[str, str]]:
    """Retrieve display labels while the user is configuring the integration."""
    result = await StrasbourgParkingsApiClient(hass).async_get_parkings()
    return [
        {"value": parking_id, "label": parking["name"]}
        for parking_id, parking in sorted(
            result.parkings.items(), key=lambda item: str(item[1]["name"]).casefold()
        )
    ]


def _selection_schema(
    parking_options: list[dict[str, str]],
    selected_parkings: list[str] | None = None,
    scan_interval: int | None = None,
) -> vol.Schema:
    """Create the identical setup/options selector schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_PARKINGS, default=selected_parkings or []
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(options=parking_options, multiple=True)
            ),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=(
                    scan_interval
                    if scan_interval is not None
                    else DEFAULT_SCAN_INTERVAL_MINUTES
                ),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(
                    min=MIN_SCAN_INTERVAL_MINUTES,
                    max=MAX_SCAN_INTERVAL_MINUTES,
                ),
            ),
        }
    )


def _as_string_list(value: Any) -> list[str]:
    """Normalize Home Assistant multi-select values."""
    if not isinstance(value, list):
        value = [value] if value else []
    return list(dict.fromkeys(str(item) for item in value if item))
