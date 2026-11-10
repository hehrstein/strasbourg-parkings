"""Open/closed sensors for Strasbourg public car parks."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import StrasbourgParkingsCoordinator
from .sensor import StrasbourgParkingEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one open/closed binary sensor per selected facility."""
    coordinator: StrasbourgParkingsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            StrasbourgParkingOpenSensor(coordinator, entry, parking_id)
            for parking_id in coordinator.parking_ids
        ]
    )


class StrasbourgParkingOpenSensor(StrasbourgParkingEntity, BinarySensorEntity):
    """Expose whether a municipal car park is open."""

    _attr_icon = "mdi:garage-open-variant"
    _attr_name = "Ouvert"

    def __init__(
        self,
        coordinator: StrasbourgParkingsCoordinator,
        entry: ConfigEntry,
        parking_id: str,
    ) -> None:
        """Initialize the parking open-state entity."""
        super().__init__(coordinator, entry, parking_id)
        self._attr_unique_id = f"{entry.entry_id}_{parking_id.casefold()}_open"

    @property
    def is_on(self) -> bool | None:
        """Return the explicit open state from the source when available."""
        parking = self._parking_data
        return parking.get("is_open") if parking else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return the same contextual details as the availability sensor."""
        return self._parking_attributes
