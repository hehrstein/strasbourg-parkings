"""Availability sensors for Strasbourg public car parks."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_ATTRIBUTION, DATA_SOURCE_URL, DOMAIN
from .coordinator import StrasbourgParkingsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one free-space sensor for each selected parking facility."""
    coordinator: StrasbourgParkingsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            StrasbourgParkingAvailabilitySensor(coordinator, entry, parking_id)
            for parking_id in coordinator.parking_ids
        ]
    )


class StrasbourgParkingEntity(CoordinatorEntity[StrasbourgParkingsCoordinator]):
    """Shared implementation for entities representing one municipal parking."""

    _attr_attribution = DATA_ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StrasbourgParkingsCoordinator,
        entry: ConfigEntry,
        parking_id: str,
    ) -> None:
        """Initialize the entity with a stable Open Data identifier."""
        super().__init__(coordinator)
        self._parking_id = parking_id
        parking = self._parking_data or {}
        parking_name = parking.get("name") or parking_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, parking_id)},
            name=f"Strasbourg — {parking_name}",
            manufacturer="Eurométropole de Strasbourg",
            model="Parking public",
            configuration_url=DATA_SOURCE_URL,
        )

    @property
    def _parking_data(self) -> dict[str, Any] | None:
        """Return the current source record for this facility."""
        parking = self.coordinator.data.get("parkings", {}).get(self._parking_id)
        return parking if isinstance(parking, dict) else None

    @property
    def _parking_attributes(self) -> dict[str, Any]:
        """Expose source values without changing their meaning."""
        parking = self._parking_data
        if parking is None:
            return {
                "parking_id": self._parking_id,
                "data_source": DATA_ATTRIBUTION,
                "data_updated_at": self.coordinator.data.get("fetched_at"),
            }

        return {
            "parking_id": self._parking_id,
            "parking_name": parking.get("name"),
            "total_capacity": parking.get("total_capacity"),
            "free_spaces": parking.get("free_spaces"),
            "occupancy_percentage": parking.get("occupancy_percentage"),
            "status": parking.get("status"),
            "status_code": parking.get("status_code"),
            "realtime_status": parking.get("realtime_status"),
            "display_status": parking.get("display_status"),
            "display_free_spaces": parking.get("display_free_spaces"),
            "occupancy_color": parking.get("occupancy_color"),
            "latitude": parking.get("latitude"),
            "longitude": parking.get("longitude"),
            "data_source": DATA_ATTRIBUTION,
            "data_updated_at": self.coordinator.data.get("fetched_at"),
        }


class StrasbourgParkingAvailabilitySensor(StrasbourgParkingEntity, SensorEntity):
    """Expose the live number of free spaces in a car park."""

    _attr_icon = "mdi:parking"
    _attr_name = "Places disponibles"
    _attr_native_unit_of_measurement = "places"

    def __init__(
        self,
        coordinator: StrasbourgParkingsCoordinator,
        entry: ConfigEntry,
        parking_id: str,
    ) -> None:
        """Initialize the free-space sensor."""
        super().__init__(coordinator, entry, parking_id)
        self._attr_unique_id = f"{entry.entry_id}_{parking_id.casefold()}_free_spaces"

    @property
    def native_value(self) -> int | None:
        """Return the spaces shown as free by the source."""
        parking = self._parking_data
        return parking.get("free_spaces") if parking else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return capacity, status and source freshness details."""
        return self._parking_attributes
