"""Sensors for monitored TrainTrack connections."""

from __future__ import annotations

from datetime import date, timedelta
from hashlib import blake2s
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback, current_platform
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util, slugify

from .const import (
    CONF_ONE_TIME_RETENTION_DAYS,
    DEFAULT_ONE_TIME_RETENTION_DAYS,
    DOMAIN,
)
from .coordinator import TrainTrackCoordinator

SENSOR_DOMAIN = "sensor"
SENSOR_ENTITY_PREFIX = f"{SENSOR_DOMAIN}."

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
    platform = current_platform.get()
    known_connection_ids: set[str] = set()
    retention_days = int(
        entry.options.get(CONF_ONE_TIME_RETENTION_DAYS, DEFAULT_ONE_TIME_RETENTION_DAYS)
    )

    expired = [
        connection
        for connection in coordinator.data or []
        if _is_expired_one_time_connection(connection, retention_days)
    ]
    await _async_remove_expired_connections(hass, entry, platform, expired)

    def add_new_connections() -> None:
        entities, expired_connections = _entities_for_connections(
            hass,
            entry,
            coordinator,
            coordinator.data or [],
            known_connection_ids,
            retention_days,
        )
        if entities:
            async_add_entities(entities)
        if expired_connections:
            hass.async_create_task(
                _async_remove_expired_connections(
                    hass, entry, platform, expired_connections
                )
            )
            known_connection_ids.difference_update(
                str(connection.get("id")) for connection in expired_connections
            )

    add_new_connections()
    entry.async_on_unload(coordinator.async_add_listener(add_new_connections))


def _entities_for_connections(
    hass: HomeAssistant,
    entry: Any,
    coordinator: TrainTrackCoordinator,
    connections: list[dict[str, Any]],
    known_connection_ids: set[str],
    retention_days: int,
) -> tuple[list[TrainTrackConnectionSensor], list[dict[str, Any]]]:
    """Create new entities and return already-added connections now expired."""
    entities: list[TrainTrackConnectionSensor] = []
    expired_connections: list[dict[str, Any]] = []
    for connection in connections:
        connection_id = str(connection.get("id", ""))
        if not connection_id:
            continue
        if _is_expired_one_time_connection(connection, retention_days):
            if connection_id in known_connection_ids:
                expired_connections.append(connection)
            continue
        _refresh_registered_device_name(hass, entry, connection)
        _refresh_registered_entity_ids(hass, entry, connection)
        if connection_id in known_connection_ids:
            continue
        known_connection_ids.add(connection_id)
        entities.extend(
            TrainTrackConnectionSensor(coordinator, entry, connection, description)
            for description in SENSORS
        )
    return entities, expired_connections


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


def _refresh_registered_entity_ids(
    hass: HomeAssistant, entry: Any, connection: dict[str, Any]
) -> None:
    """Give new sensors stable IDs and migrate recognizable generated IDs."""
    connection_id = str(connection.get("id", ""))
    if not connection_id:
        return
    origin = connection.get("origin") or "Unbekannter Start"
    destination = connection.get("destination") or "Unbekanntes Ziel"
    legacy_object_id = slugify(f"{origin} {destination}")
    route_only_object_id = slugify(f"{origin} → {destination}")
    route_object_id = slugify(_connection_name(connection))
    schedule_object_id = route_object_id.removeprefix(route_only_object_id).lstrip("_")
    registry = er.async_get(hass)
    for description in SENSORS:
        sensor_key = description.key
        unique_id = f"{entry.unique_id}_{connection_id}_{sensor_key}"
        suggested_object_id = _stable_entity_object_id(entry.unique_id, connection_id, sensor_key)
        target_entity_id = f"{SENSOR_ENTITY_PREFIX}{suggested_object_id}"
        registered_entity_id = registry.async_get_entity_id(SENSOR_DOMAIN, DOMAIN, unique_id)
        if registered_entity_id is None:
            registry.async_get_or_create(
                SENSOR_DOMAIN,
                DOMAIN,
                unique_id,
                config_entry=entry,
                suggested_object_id=suggested_object_id,
                has_entity_name=True,
                translation_key=description.translation_key,
            )
            continue
        entity_object_id = registered_entity_id.removeprefix(SENSOR_ENTITY_PREFIX)
        if registered_entity_id == target_entity_id or not _is_generated_entity_id(
            entity_object_id,
            sensor_key,
            legacy_object_id,
            route_object_id,
            schedule_object_id,
        ):
            continue
        try:
            available_entity_id = registry.async_get_available_entity_id(
                SENSOR_DOMAIN,
                suggested_object_id,
                current_entity_id=registered_entity_id,
            )
            registry.async_update_entity(
                registered_entity_id, new_entity_id=available_entity_id
            )
        except (ValueError, KeyError):
            # A conflicting or manually occupied target ID must not block setup.
            continue


def _stable_entity_object_id(
    entry_unique_id: str, connection_id: str, sensor_key: str
) -> str:
    """Identify a sensor without putting changeable schedule text in its ID."""
    digest = blake2s(
        f"{entry_unique_id}\0{connection_id}".encode(), digest_size=8
    ).hexdigest()
    return f"traintrack_{sensor_key}_{digest}"


def _is_generated_entity_id(
    object_id: str,
    sensor_key: str,
    legacy_object_id: str,
    route_object_id: str,
    schedule_object_id: str,
) -> bool:
    """Recognize our old IDs, including repeated or truncated schedules."""
    for prefix in (legacy_object_id, route_object_id):
        if object_id in {prefix, f"{prefix}_{sensor_key}"}:
            return True
        for candidate in (prefix, f"{prefix}_{sensor_key}"):
            if object_id.startswith(f"{candidate}_") and object_id[
                len(candidate) + 1 :
            ].isdigit():
                return True
    if schedule_object_id and object_id.startswith(
        f"{route_object_id}_{schedule_object_id}"
    ):
        return True
    return object_id.startswith(f"{route_object_id}_{route_object_id}")


def _is_expired_one_time_connection(
    connection: dict[str, Any], retention_days: int
) -> bool:
    """Return whether a completed one-time trip passed its retention period."""
    if connection.get("connectionType") != "one_time":
        return False
    service_date = connection.get("serviceDate")
    if not isinstance(service_date, str):
        return False
    try:
        last_retained_date = date.fromisoformat(service_date) + timedelta(days=retention_days)
    except ValueError:
        return False
    return dt_util.now().date() > last_retained_date


async def _async_remove_expired_connections(
    hass: HomeAssistant, entry: Any, platform: Any, connections: list[dict[str, Any]]
) -> None:
    """Remove expired one-time trips and their entities/devices from HA registries."""
    if not connections:
        return
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    for connection in connections:
        connection_id = str(connection.get("id", ""))
        if not connection_id:
            continue
        unique_id_prefix = f"{entry.unique_id}_{connection_id}_"
        registered_entities = [
            entity
            for entity in er.async_entries_for_config_entry(
                entity_registry, entry.entry_id
            )
            if entity.unique_id.startswith(unique_id_prefix)
        ]
        for entity in registered_entities:
            if platform is not None and entity.entity_id in platform.entities:
                await platform.async_remove_entity(entity.entity_id)
            entity_registry.async_remove(entity.entity_id)

        identifier = f"{entry.unique_id}_{connection_id}"
        device = device_registry.async_get_device_by_identifier(
            (DOMAIN, identifier), entry.entry_id
        )
        if device is not None:
            device_registry.async_remove_device(device.id)


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
