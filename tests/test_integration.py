"""Focused integration tests using small Home Assistant API stubs."""

from __future__ import annotations

import asyncio
import importlib
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch


def _module(name: str, **attributes):
    module = types.ModuleType(name)
    module.__dict__.update(attributes)
    module.__path__ = []
    sys.modules[name] = module
    return module


class _Schema:
    def __init__(self, schema):
        self.schema = schema


class _ConfigFlow:
    def __init_subclass__(cls, **_kwargs):
        return super().__init_subclass__()

    def __init__(self):
        self.hass = None
        self.context = {}

    async def async_set_unique_id(self, value):
        self.unique_id = value

    def _abort_if_unique_id_configured(self):
        return None

    def _abort_if_unique_id_mismatch(self):
        return None

    def _get_reconfigure_entry(self):
        return self.entry

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    def async_update_reload_and_abort(self, entry, **kwargs):
        return {"type": "update", "entry": entry, **kwargs}

    def async_abort(self, **kwargs):
        return {"type": "abort", **kwargs}


class _OptionsFlow(_ConfigFlow):
    pass


class _DataUpdateCoordinator:
    @classmethod
    def __class_getitem__(cls, _):
        return cls

    def __init__(self, hass, **kwargs):
        self.hass = hass
        self.options = kwargs
        self.data = None
        self.last_update_success = True
        self.listeners = []

    def async_add_listener(self, callback):
        self.listeners.append(callback)
        return lambda: None

    async def async_config_entry_first_refresh(self):
        self.data = await self._async_update_data()


class _CoordinatorEntity:
    @classmethod
    def __class_getitem__(cls, _):
        return cls

    def __init__(self, coordinator):
        self.coordinator = coordinator


class _SensorEntity:
    pass


class _SensorEntityDescription:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _DeviceInfo(dict):
    pass


class _FakeDeviceRegistry:
    def __init__(self, devices=None):
        self.devices = devices or {}
        self.updates = []

    def async_get_device_by_identifier(self, identifier, entry_id):
        return self.devices.get((identifier, entry_id))

    def async_update_device(self, device_id, **kwargs):
        self.updates.append((device_id, kwargs))
        for device in self.devices.values():
            if device.id == device_id:
                for key, value in kwargs.items():
                    setattr(device, key, value)
                return device
        raise AssertionError(f"Unknown device id: {device_id}")

    def async_remove_device(self, device_id):
        self.devices = {
            key: device for key, device in self.devices.items() if device.id != device_id
        }


class _FakeEntityRegistry:
    def __init__(self, entries=None):
        self.entries = entries or []
        self.updates = []
        self.removals = []

    def async_entries_for_config_entry(self, entry_id):
        return [item for item in self.entries if item.config_entry_id == entry_id]

    def async_update_entity(self, entity_id, **kwargs):
        self.updates.append((entity_id, kwargs))

    def async_remove(self, entity_id):
        self.removals.append(entity_id)
        self.entries = [item for item in self.entries if item.entity_id != entity_id]


class _Selector:
    def __init__(self, config=None):
        self.config = config


class _NumberSelectorConfig:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _TextSelectorConfig:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status = status
        self.payload = payload if payload is not None else {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def json(self, **_):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class _SlowResponse(_FakeResponse):
    async def __aenter__(self):
        await asyncio.sleep(0.02)
        return self


class _FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response or _FakeResponse(payload={})
        self.error = error
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return self.response


class _HomeAssistantError(Exception):
    pass


class _ConfigEntryAuthFailed(_HomeAssistantError):
    pass


class _UpdateFailed(Exception):
    pass


def _install_home_assistant_stubs():
    class ClientError(Exception):
        pass

    _module("aiohttp", ClientError=ClientError, ClientSession=_FakeSession)
    _module("voluptuous", Schema=_Schema, Required=lambda key, **_: key)
    _module("homeassistant")
    _module("homeassistant.config_entries", ConfigEntry=object, ConfigFlow=_ConfigFlow, OptionsFlow=_OptionsFlow)
    _module("homeassistant.core", HomeAssistant=object)
    _module(
        "homeassistant.exceptions",
        ConfigEntryAuthFailed=_ConfigEntryAuthFailed,
        HomeAssistantError=_HomeAssistantError,
    )
    _module("homeassistant.helpers")
    _module("homeassistant.helpers.aiohttp_client", async_get_clientsession=lambda hass: hass.session)
    _module(
        "homeassistant.helpers.selector",
        NumberSelector=_Selector,
        NumberSelectorConfig=_NumberSelectorConfig,
        NumberSelectorMode=types.SimpleNamespace(BOX="box"),
        TextSelector=_Selector,
        TextSelectorConfig=_TextSelectorConfig,
        TextSelectorType=types.SimpleNamespace(PASSWORD="password"),
    )
    _module(
        "homeassistant.helpers.device_registry",
        DeviceInfo=_DeviceInfo,
        async_get=lambda hass: hass.device_registry,
    )
    _module(
        "homeassistant.helpers.entity_registry",
        async_get=lambda hass: hass.entity_registry,
    )
    _module(
        "homeassistant.helpers.entity_platform",
        AddEntitiesCallback=object,
        current_platform=types.SimpleNamespace(get=lambda: None),
    )
    _module(
        "homeassistant.helpers.update_coordinator",
        DataUpdateCoordinator=_DataUpdateCoordinator,
        CoordinatorEntity=_CoordinatorEntity,
        UpdateFailed=_UpdateFailed,
    )
    _module("homeassistant.components")
    _module(
        "homeassistant.components.sensor",
        SensorEntity=_SensorEntity,
        SensorEntityDescription=_SensorEntityDescription,
    )
    util = _module(
        "homeassistant.util",
        slugify=lambda value: value.lower().replace(" → ", "_").replace(" ", "_"),
    )
    util.dt = types.SimpleNamespace(now=lambda: datetime.now(timezone.utc))


_install_home_assistant_stubs()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
api = importlib.import_module("custom_components.traintrack.api")
config_flow = importlib.import_module("custom_components.traintrack.config_flow")
coordinator_module = importlib.import_module("custom_components.traintrack.coordinator")
integration = importlib.import_module("custom_components.traintrack")
sensor_module = importlib.import_module("custom_components.traintrack.sensor")


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_api_key_is_sent_to_documented_routes(self):
        session = _FakeSession(_FakeResponse(payload={"user": {"id": "owner"}}))
        client = api.TrainTrackApi(session, "https://train.example/base", "secret")
        self.assertEqual(await client.async_get_user(), {"id": "owner"})
        url, kwargs = session.calls[0]
        self.assertEqual(url, "https://train.example/base/api/session")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertFalse(kwargs["allow_redirects"])

    async def test_connections_and_invalid_payloads(self):
        client = api.TrainTrackApi(
            _FakeSession(_FakeResponse(payload={"connections": [{"id": "one"}]})),
            "https://train.example",
            "secret",
        )
        self.assertEqual(await client.async_get_connections(), [{"id": "one"}])
        invalid_user = api.TrainTrackApi(_FakeSession(_FakeResponse(payload={})), "https://train.example", "secret")
        with self.assertRaises(api.TrainTrackConnectionError):
            await invalid_user.async_get_user()
        invalid_connections = api.TrainTrackApi(
            _FakeSession(_FakeResponse(payload={"connections": [None]})), "https://train.example", "secret"
        )
        with self.assertRaises(api.TrainTrackConnectionError):
            await invalid_connections.async_get_connections()

    async def test_http_auth_failure_and_bad_response(self):
        for status in (401, 403):
            client = api.TrainTrackApi(_FakeSession(_FakeResponse(status, {})), "https://train.example", "secret")
            with self.assertRaises(api.TrainTrackAuthError):
                await client.async_get_user()
        client = api.TrainTrackApi(_FakeSession(_FakeResponse(503, {})), "https://train.example", "secret")
        with self.assertRaises(api.TrainTrackConnectionError):
            await client.async_get_user()
        client = api.TrainTrackApi(_FakeSession(_FakeResponse(payload=[])), "https://train.example", "secret")
        with self.assertRaises(api.TrainTrackConnectionError):
            await client.async_get_user()

    async def test_network_and_json_errors_are_normalized(self):
        client_error = sys.modules["aiohttp"].ClientError("offline")
        client = api.TrainTrackApi(_FakeSession(error=client_error), "https://train.example", "secret")
        with self.assertRaises(api.TrainTrackConnectionError):
            await client.async_get_user()

    async def test_request_timeout_is_normalized(self):
        client = api.TrainTrackApi(_FakeSession(_SlowResponse()), "https://train.example", "secret")
        with patch.object(api, "REQUEST_TIMEOUT_SECONDS", 0.001):
            with self.assertRaises(api.TrainTrackConnectionError):
                await client.async_get_user()
        client = api.TrainTrackApi(
            _FakeSession(_FakeResponse(payload=ValueError("invalid json"))), "https://train.example", "secret"
        )
        with self.assertRaises(api.TrainTrackConnectionError):
            await client.async_get_user()


class ConfigFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_user_flow_validates_and_stores_key_and_interval(self):
        flow = config_flow.TrainTrackConfigFlow()
        flow.hass = types.SimpleNamespace(session=_FakeSession(
            _FakeResponse(payload={"user": {"id": "owner"}})
        ))
        result = await flow.async_step_user({"base_url": "https://train.example/", "api_key": "secret", "scan_interval": 600})
        self.assertEqual(result["data"]["api_key"], "secret")
        self.assertEqual(result["data"]["scan_interval"], 600)
        self.assertEqual(flow.unique_id, "owner")

    async def test_user_flow_reports_url_auth_and_connection_errors(self):
        flow = config_flow.TrainTrackConfigFlow()
        flow.hass = types.SimpleNamespace(session=_FakeSession())
        base = {"base_url": "ftp://remote.example", "api_key": "secret", "scan_interval": 300}
        self.assertEqual((await flow.async_step_user(base))["errors"]["base"], "invalid_url")
        base["base_url"] = "https://train.example"
        base["api_key"] = ""
        self.assertEqual((await flow.async_step_user(base))["errors"]["base"], "invalid_auth")
        base["api_key"] = "secret"
        flow.hass.session = _FakeSession(_FakeResponse(401, {}))
        self.assertEqual((await flow.async_step_user(base))["errors"]["base"], "invalid_auth")
        flow.hass.session = _FakeSession(error=sys.modules["aiohttp"].ClientError("offline"))
        self.assertEqual((await flow.async_step_user(base))["errors"]["base"], "cannot_connect")
        base["base_url"] = "https://user@train.example"
        self.assertEqual((await flow.async_step_user(base))["errors"]["base"], "invalid_url")
        base["base_url"] = "http://localhost:8080"
        flow.hass.session = _FakeSession(_FakeResponse(payload={"user": {"id": "local"}}))
        self.assertEqual((await flow.async_step_user(base))["data"]["base_url"], base["base_url"])
        base["base_url"] = "http://remote.example:9123"
        self.assertEqual((await flow.async_step_user(base))["data"]["base_url"], base["base_url"])
        base["base_url"] = "http://remote.example:invalid"
        self.assertEqual((await flow.async_step_user(base))["errors"]["base"], "invalid_url")

    async def test_reconfigure_and_reauthentication_replace_credentials(self):
        entry = types.SimpleNamespace(data={"base_url": "https://old.example", "api_key": "old"})
        session = _FakeSession(_FakeResponse(payload={"user": {"id": "owner"}}))
        flow = config_flow.TrainTrackConfigFlow()
        flow.entry = entry
        flow.context = {"entry_id": "entry"}
        flow.hass = types.SimpleNamespace(
            session=session,
            config_entries=types.SimpleNamespace(async_get_entry=lambda _: entry),
        )
        form = await flow.async_step_reconfigure()
        self.assertEqual(form["step_id"], "reconfigure")
        updated = await flow.async_step_reconfigure({"base_url": "https://new.example", "api_key": "new"})
        self.assertEqual(updated["data_updates"]["api_key"], "new")
        updated_http = await flow.async_step_reconfigure({"base_url": "http://other.example:8080", "api_key": "new"})
        self.assertEqual(updated_http["data_updates"]["base_url"], "http://other.example:8080")
        reauth = await flow.async_step_reauth({})
        self.assertEqual(reauth["step_id"], "reauth_confirm")
        replaced = await flow.async_step_reauth_confirm({"base_url": "https://new.example", "api_key": "new"})
        self.assertEqual(replaced["data_updates"]["api_key"], "new")
        failed_reauth = await flow.async_step_reauth_confirm({"base_url": "https://new.example", "api_key": ""})
        self.assertEqual(failed_reauth["errors"]["base"], "invalid_auth")

    async def test_user_form_and_missing_reauth_entry(self):
        flow = config_flow.TrainTrackConfigFlow()
        flow.hass = types.SimpleNamespace(session=_FakeSession())
        self.assertEqual((await flow.async_step_user())["step_id"], "user")
        flow.context = {"entry_id": "missing"}
        flow.hass.config_entries = types.SimpleNamespace(async_get_entry=lambda _: None)
        self.assertEqual((await flow.async_step_reauth({}))['reason'], "reauth_entry_not_found")

    async def test_options_flow_saves_poll_interval(self):
        entry = types.SimpleNamespace(options={}, data={"scan_interval": 300})
        flow = config_flow.TrainTrackOptionsFlow(entry)
        form = await flow.async_step_init()
        self.assertEqual(form["step_id"], "init")
        result = await flow.async_step_init({"scan_interval": 900, "one_time_retention_days": 14})
        self.assertEqual(result["data"]["scan_interval"], 900)
        self.assertEqual(result["data"]["one_time_retention_days"], 14)
        self.assertEqual(config_flow._scan_interval_selector().config.step, 30)
        self.assertEqual(config_flow._one_time_retention_selector().config.max, 365)


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_poll_interval_prefers_options_then_config(self):
        entry = types.SimpleNamespace(data={"base_url": "https://train", "api_key": "k", "scan_interval": 300}, options={"scan_interval": 600})
        coordinator = coordinator_module.TrainTrackCoordinator(types.SimpleNamespace(), entry, api=types.SimpleNamespace())
        self.assertEqual(coordinator.options["update_interval"], timedelta(seconds=600))
        entry.options = {}
        coordinator = coordinator_module.TrainTrackCoordinator(types.SimpleNamespace(), entry, api=types.SimpleNamespace())
        self.assertEqual(coordinator.options["update_interval"], timedelta(seconds=300))
        entry.data = {"base_url": "https://train", "api_key": "k"}
        hass = types.SimpleNamespace(session=_FakeSession())
        coordinator = coordinator_module.TrainTrackCoordinator(hass, entry)
        self.assertEqual(coordinator.options["update_interval"], timedelta(seconds=300))
        self.assertIsInstance(coordinator.api, api.TrainTrackApi)

    async def test_update_errors_become_home_assistant_recoverable_errors(self):
        entry = types.SimpleNamespace(data={}, options={})
        fake_api = types.SimpleNamespace(async_get_connections=AsyncMock(return_value=[{"id": "x"}]))
        coordinator = coordinator_module.TrainTrackCoordinator(types.SimpleNamespace(), entry, api=fake_api)
        self.assertEqual(await coordinator._async_update_data(), [{"id": "x"}])
        fake_api.async_get_connections.side_effect = api.TrainTrackAuthError()
        with self.assertRaises(_ConfigEntryAuthFailed):
            await coordinator._async_update_data()
        fake_api.async_get_connections.side_effect = api.TrainTrackConnectionError()
        with self.assertRaises(_UpdateFailed):
            await coordinator._async_update_data()
        fake_api.async_get_connections.side_effect = _HomeAssistantError()
        with self.assertRaises(_UpdateFailed):
            await coordinator._async_update_data()


class SetupAndSensorTests(unittest.IsolatedAsyncioTestCase):
    def test_one_time_connection_name_includes_departure_and_service_date(self):
        name = sensor_module._connection_name(
            {
                "origin": "C",
                "destination": "D",
                "departureTime": "09:15",
                "connectionType": "one_time",
                "serviceDate": "2026-10-15",
            }
        )
        self.assertEqual(name, "C → D · 09:15 · 2026-10-15")

    def test_one_time_retention_uses_configured_grace_period(self):
        connection = {
            "connectionType": "one_time",
            "serviceDate": "2026-10-01",
        }
        with patch.object(
            sensor_module.dt_util,
            "now",
            return_value=datetime(2026, 10, 8, tzinfo=timezone.utc),
        ):
            self.assertFalse(sensor_module._is_expired_one_time_connection(connection, 7))
            self.assertTrue(sensor_module._is_expired_one_time_connection(connection, 6))
            self.assertFalse(
                sensor_module._is_expired_one_time_connection(
                    {**connection, "serviceDate": "not-a-date"}, 1
                )
            )
            self.assertFalse(
                sensor_module._is_expired_one_time_connection(
                    {**connection, "connectionType": "weekly"}, 1
                )
            )

    async def test_entry_migration_replaces_cookie_and_sets_interval(self):
        saved = {}
        entry = types.SimpleNamespace(
            version=1,
            data={"base_url": "https://train", "session_token": "old"},
        )
        hass = types.SimpleNamespace(config_entries=types.SimpleNamespace(
            async_update_entry=lambda _entry, **kwargs: (saved.update(kwargs), setattr(entry, "version", kwargs["version"]))
        ))
        self.assertTrue(await integration.async_migrate_entry(hass, entry))
        self.assertNotIn("session_token", saved["data"])
        self.assertEqual(saved["data"]["scan_interval"], 300)
        self.assertEqual(saved["data"]["api_key"], "")
        self.assertFalse(await integration.async_migrate_entry(hass, types.SimpleNamespace(version=3, data={})))

    async def test_setup_and_unload_entry(self):
        coordinator = types.SimpleNamespace(
            async_config_entry_first_refresh=AsyncMock(),
            async_add_listener=lambda callback: lambda: None,
            data=[],
        )
        original = integration.TrainTrackCoordinator
        integration.TrainTrackCoordinator = lambda *_: coordinator
        entry = types.SimpleNamespace(
            entry_id="entry",
            add_update_listener=lambda callback: callback,
            async_on_unload=lambda callback: None,
        )
        hass = types.SimpleNamespace(
            data={},
            config_entries=types.SimpleNamespace(
                async_forward_entry_setups=AsyncMock(),
                async_unload_platforms=AsyncMock(return_value=True),
                async_reload=AsyncMock(),
            ),
        )
        try:
            self.assertTrue(await integration.async_setup_entry(hass, entry))
            self.assertIs(hass.data["traintrack"]["entry"], coordinator)
            self.assertTrue(await integration.async_unload_entry(hass, entry))
            self.assertNotIn("entry", hass.data["traintrack"])
            await integration.async_reload_entry(hass, entry)
        finally:
            integration.TrainTrackCoordinator = original

    async def test_sensor_setup_adds_new_connections_and_exposes_values(self):
        route = {
            "id": "connection",
            "origin": "A",
            "destination": "B",
            "departureTime": "08:00",
            "arrivalTimesByWeekday": {"1": "09:05"},
            "weekdays": [1, 3],
            "connectionType": "weekly",
            "groupPosition": 2,
            "transferFromPrevious": "Umstieg Gleis 4",
            "status": {
                "status": "delayed",
                "message": "Gleisänderung",
                "train": "RE1",
                "delayMinutes": 5,
                "checkedAt": "2026-10-14T08:00:00+02:00",
                "tripId": "trip-1",
                "plannedPlatform": "3",
                "changeDetails": ["Gleis 3 statt 2"],
                "urgency": "elevated",
            },
            "history": [],
            "observations": [],
        }
        coordinator = _DataUpdateCoordinator(None)
        coordinator.data = [route]
        added = []
        entry = types.SimpleNamespace(
            entry_id="entry", unique_id="owner", options={}, async_on_unload=lambda _: None
        )
        device = types.SimpleNamespace(
            id="registered-device",
            name="A → B",
            name_by_user=None,
        )
        registry = _FakeDeviceRegistry({(("traintrack", "owner_connection"), "entry"): device})
        hass = types.SimpleNamespace(
            data={"traintrack": {"entry": coordinator}},
            device_registry=registry,
            entity_registry=_FakeEntityRegistry(),
        )
        await sensor_module.async_setup_entry(hass, entry, added.extend)
        self.assertEqual(len(added), 3)
        self.assertEqual(device.name, "A → B · 08:00 · Mo, Mi · Abschnitt 2")
        self.assertEqual(
            registry.updates,
            [("registered-device", {"name": "A → B · 08:00 · Mo, Mi · Abschnitt 2"})],
        )
        entity = added[2]
        self.assertEqual(entity.native_value, 5)
        self.assertEqual(added[0].native_value, "delayed")
        self.assertEqual(added[1].native_value, "RE1")
        self.assertTrue(entity.available)
        self.assertEqual(entity.extra_state_attributes["origin"], "A")
        self.assertEqual(entity.extra_state_attributes["arrival_times_by_weekday"], {"1": "09:05"})
        self.assertEqual(entity.extra_state_attributes["status_message"], "Gleisänderung")
        self.assertEqual(entity.extra_state_attributes["planned_platform"], "3")
        self.assertEqual(entity.extra_state_attributes["transfer_from_previous"], "Umstieg Gleis 4")
        self.assertEqual(entity.extra_state_attributes["route"], "A → B · 08:00 · Mo, Mi · Abschnitt 2")
        self.assertEqual(entity._attr_device_info["manufacturer"], "TrainTrack")
        self.assertIn("08:00", entity._attr_device_info["name"])
        self.assertIn("Mo, Mi", entity._attr_device_info["name"])
        coordinator.listeners[0]()
        self.assertEqual(len(added), 3)
        coordinator.data = []
        self.assertFalse(entity.available)
        self.assertEqual(entity.native_value, 5)
        coordinator.data = [{**route, "status": {}}]
        self.assertEqual(added[0].native_value, "waiting")
        self.assertIsNone(added[1].native_value)
        self.assertIsNone(added[2].native_value)

    def test_registered_device_name_refresh_preserves_user_name(self):
        device = types.SimpleNamespace(
            id="registered-device",
            name="My Train",
            name_by_user="My Train",
        )
        registry = _FakeDeviceRegistry({(("traintrack", "owner_connection"), "entry"): device})
        hass = types.SimpleNamespace(device_registry=registry)
        entry = types.SimpleNamespace(entry_id="entry", unique_id="owner")

        sensor_module._refresh_registered_device_name(
            hass,
            entry,
            {"id": "connection", "origin": "A", "destination": "B", "departureTime": "08:00"},
        )

        self.assertEqual(device.name, "My Train")
        self.assertEqual(registry.updates, [])

    def test_registered_entity_ids_gain_schedule_details(self):
        entity = types.SimpleNamespace(
            config_entry_id="entry",
            unique_id="owner_connection_status",
            entity_id="sensor.a_b",
        )
        registry = _FakeEntityRegistry([entity])
        hass = types.SimpleNamespace(entity_registry=registry)
        entry = types.SimpleNamespace(entry_id="entry", unique_id="owner")
        sensor_module._refresh_registered_entity_ids(
            hass,
            entry,
            {
                "id": "connection",
                "origin": "A",
                "destination": "B",
                "departureTime": "08:00",
                "weekdays": [1],
            },
        )
        target_id = f"sensor.{sensor_module.slugify(sensor_module._connection_name({
            'origin': 'A', 'destination': 'B', 'departureTime': '08:00', 'weekdays': [1]
        }))}"
        self.assertEqual(
            registry.updates,
            [("sensor.a_b", {"new_entity_id": target_id})],
        )

    async def test_expired_connections_remove_entities_and_devices(self):
        registered_entity = types.SimpleNamespace(
            config_entry_id="entry",
            unique_id="owner_trip_status",
            entity_id="sensor.old_trip_status",
        )
        entity_registry = _FakeEntityRegistry([registered_entity])
        device = types.SimpleNamespace(id="trip-device")
        device_registry = _FakeDeviceRegistry(
            {(("traintrack", "owner_trip"), "entry"): device}
        )
        hass = types.SimpleNamespace(
            entity_registry=entity_registry,
            device_registry=device_registry,
        )
        entry = types.SimpleNamespace(entry_id="entry", unique_id="owner")
        platform = types.SimpleNamespace(
            entities={"sensor.old_trip_status": object()},
            removed=[],
        )

        async def remove_entity(entity_id):
            platform.removed.append(entity_id)
            platform.entities.pop(entity_id)

        platform.async_remove_entity = remove_entity
        await sensor_module._async_remove_expired_connections(
            hass,
            entry,
            platform,
            [{"id": "trip", "connectionType": "one_time", "serviceDate": "2026-01-01"}],
        )
        self.assertEqual(entity_registry.removals, ["sensor.old_trip_status"])
        self.assertEqual(platform.removed, ["sensor.old_trip_status"])
        self.assertEqual(device_registry.devices, {})


if __name__ == "__main__":
    unittest.main()
