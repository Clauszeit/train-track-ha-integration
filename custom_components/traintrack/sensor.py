"""Sensors for monitored TrainTrack connections."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
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

WEEKDAY_LABELS = {
    1: "Mo",
    2: "Di",
    3: "Mi",
    4: "Do",
    5: "Fr",
    6: "Sa",
    7: "So",
}


def _connection_name(connection: dict[str, Any]) -> str:
    """Build a device name that distinguishes routes by their schedule."""
    origin = connection.get("origin") or "Unbekannter Start"
    destination = connection.get("destination") or "Unbekanntes Ziel"
    name = f"{origin} → {destination}"
    departure_time = connection.get("departureTime")
    if departure_time:
        name += f" · {departure_time}"

    if connection.get("connectionType") == "one_time":
        if connection.get("serviceDate"):
            name += f" · {connection['serviceDate']}"
    else:
        weekdays = connection.get("weekdays")
        if isinstance(weekdays, list):
            labels = [WEEKDAY_LABELS[day] for day in weekdays if day in WEEKDAY_LABELS]
            if labels:
                name += f" · {', '.join(labels)}"

    group_position = connection.get("groupPosition")
    if isinstance(group_position, int):
        name += f" · Abschnitt {group_position}"
    return name


async def async_setup_entry(  # NOSONAR(S7503)
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
            if not connection_id:
                continue
            _refresh_registered_device_name(hass, entry, connection)
            if connection_id in known_connection_ids:
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


def _refresh_registered_device_name(
    hass: HomeAssistant, entry: Any, connection: dict[str, Any]
) -> None:
    """Update old registry names while preserving names chosen by the user."""
    connection_id = str(connection.get("id", ""))
    if not connection_id:
        return

    identifier = f"{entry.unique_id}_{connection_id}"
    registry = dr.async_get(hass)
    device = registry.async_get_device_by_identifier((DOMAIN, identifier), entry.entry_id)
    if device is None or device.name_by_user is not None:
        return

    name = _connection_name(connection)
    if device.name != name:
        registry.async_update_device(device.id, name=name)


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
            name=_connection_name(connection),
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
        """Expose the full connection, schedule, and monitor payload."""
        connection = self._current_connection
        status = connection.get("status")
        if not isinstance(status, dict):
            status = {}
        attributes = dict(connection)
        attributes.update(
            {
                "connection_id": self._connection_id,
                "route": _connection_name(connection),
                "departure_time": connection.get("departureTime"),
                "arrival_times_by_weekday": connection.get("arrivalTimesByWeekday", {}),
                "connection_type": connection.get("connectionType", "weekly"),
                "service_date": connection.get("serviceDate"),
                "group_position": connection.get("groupPosition"),
                "transfer_from_previous": connection.get("transferFromPrevious"),
                "manual_selection": connection.get("manualSelection"),
                "monitor_status": status,
                "status_code": status.get("status"),
                "status_message": status.get("message"),
                "train": status.get("train"),
                "delay_minutes": status.get("delayMinutes"),
                "checked_at": status.get("checkedAt"),
                "operating_date": status.get("operatingDate"),
                "trip_id": status.get("tripId"),
                "planned_departure": status.get("plannedDeparture"),
                "planned_platform": status.get("plannedPlatform"),
                "change_station": status.get("changeStation"),
                "change_details": status.get("changeDetails", []),
                "urgency": status.get("urgency"),
                "preceding_affected_departures": status.get(
                    "precedingAffectedDepartures", 0
                ),
                "historical_context": connection.get("historicalContext"),
                "history": connection.get("history", []),
                "observations": connection.get("observations", []),
            }
        )
        return attributes

    @property
    def _current_connection(self) -> dict[str, Any]:
        for connection in self.coordinator.data or []:
            if str(connection.get("id")) == self._connection_id:
                self._route = connection
                return connection
        return self._route
