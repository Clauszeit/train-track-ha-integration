"""Sensors for monitored TrainTrack connections."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TrainTrackCoordinator

SENSORS = (
    SensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:train",
    ),
    SensorEntityDescription(
        key="train",
        translation_key="train",
        icon="mdi:train-variant",
    ),
    SensorEntityDescription(
        key="delay",
        translation_key="delay",
        icon="mdi:clock-alert-outline",
        native_unit_of_measurement="min",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one set of sensors for each monitored connection."""
    coordinator: TrainTrackCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_connection_ids: set[str] = set()

    def add_new_connections() -> None:
        entities: list[TrainTrackConnectionSensor] = []
        for connection in coordinator.data or []:
            connection_id = str(connection.get("id", ""))
            if not connection_id or connection_id in known_connection_ids:
                continue
            known_connection_ids.add(connection_id)
            entities.extend(
                TrainTrackConnectionSensor(coordinator, entry, connection, description)
                for description in SENSORS
            )
        if entities:
            async_add_entities(entities)

    add_new_connections()
    entry.async_on_unload(coordinator.async_add_listener(add_new_connections))


class TrainTrackConnectionSensor(CoordinatorEntity[TrainTrackCoordinator], SensorEntity):
    """Expose one property of a monitored connection."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrainTrackCoordinator,
        entry: Any,
        connection: dict[str, Any],
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._connection_id = str(connection["id"])
        self._route = connection
        self._attr_unique_id = f"{entry.unique_id}_{self._connection_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}_{self._connection_id}")},
            name=(
                f"{connection.get('origin', 'Unbekannt')} → "
                f"{connection.get('destination', 'Unbekannt')}"
            ),
            manufacturer="TrainTrack",
        )

    @property
    def available(self) -> bool:
        """Expose entities only for connections in the latest successful response."""
        return self.coordinator.last_update_success and any(
            str(connection.get("id")) == self._connection_id
            for connection in self.coordinator.data or []
        )

    @property
    def native_value(self) -> str | int | float | None:
        """Return the selected connection property."""
        connection = self._current_connection
        status = connection.get("status") or {}
        if self.entity_description.key == "status":
            return status.get("status", "waiting")
        if self.entity_description.key == "train":
            return status.get("train") or None
        if self.entity_description.key == "delay":
            delay = status.get("delayMinutes")
            return delay if isinstance(delay, (int, float)) else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Include route and monitor details for dashboards and automations."""
        connection = self._current_connection
        return {
            "origin": connection.get("origin"),
            "destination": connection.get("destination"),
            "departure_time": connection.get("departureTime"),
            "weekdays": connection.get("weekdays"),
            "service_date": connection.get("serviceDate"),
            "monitor_status": connection.get("status"),
            "history": connection.get("history", []),
            "observations": connection.get("observations", []),
        }

    @property
    def _current_connection(self) -> dict[str, Any]:
        for connection in self.coordinator.data or []:
            if str(connection.get("id")) == self._connection_id:
                self._route = connection
                return connection
        return self._route
