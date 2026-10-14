"""Config flow for TrainTrack."""

from __future__ import annotations

from urllib.parse import urlsplit
from typing import Any

import voluptuous as vol
from aiohttp import ClientSession
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    TrainTrackApi,
    TrainTrackAuthError,
    TrainTrackConnectionError,
)
from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_ONE_TIME_RETENTION_DAYS,
    CONF_SCAN_INTERVAL,
    DEFAULT_ONE_TIME_RETENTION_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_ONE_TIME_RETENTION_DAYS,
    MAX_SCAN_INTERVAL,
    MIN_ONE_TIME_RETENTION_DAYS,
    MIN_SCAN_INTERVAL,
)


def _schema(
    defaults: dict[str, Any] | None = None,
    include_scan_interval: bool = False,
) -> vol.Schema:
    values = defaults or {}
    schema = {
        vol.Required(CONF_BASE_URL, default=values.get(CONF_BASE_URL, "")): str,
        vol.Required(CONF_API_KEY, default=""): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
    }
    if include_scan_interval:
        schema[vol.Required(
            CONF_SCAN_INTERVAL,
            default=values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )] = _scan_interval_selector()
    return vol.Schema(schema)


def _scan_interval_selector() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=MIN_SCAN_INTERVAL,
            max=MAX_SCAN_INTERVAL,
            step=30,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement="s",
        )
    )


def _one_time_retention_selector() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=MIN_ONE_TIME_RETENTION_DAYS,
            max=MAX_ONE_TIME_RETENTION_DAYS,
            step=1,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement="d",
        )
    )


async def _validate_input(
    hass: HomeAssistant, data: dict[str, str]
) -> tuple[str | None, str | None]:
    """Return a user ID or a translatable validation error."""
    base_url = data[CONF_BASE_URL].strip().rstrip("/")
    try:
        parsed_url = urlsplit(base_url)
        port = parsed_url.port
    except ValueError:
        return None, "invalid_url"
    supported_url = (
        parsed_url.scheme in {"http", "https"}
        and bool(parsed_url.hostname)
        and (port is None or 1 <= port <= 65535)
    )
    if (
        not supported_url
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
    ):
        return None, "invalid_url"
    if not data[CONF_API_KEY].strip():
        return None, "invalid_auth"
    session: ClientSession = async_get_clientsession(hass)
    api = TrainTrackApi(session, base_url, data[CONF_API_KEY].strip())
    try:
        user = await api.async_get_user()
    except TrainTrackAuthError:
        return None, "invalid_auth"
    except TrainTrackConnectionError:
        return None, "cannot_connect"
    return user["id"], None


class TrainTrackConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TrainTrack."""

    VERSION = 2
    _reauth_entry_id: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Set up TrainTrack from the account URL and an API key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_id, error = await _validate_input(self.hass, user_input)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(user_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="TrainTrack",
                    data={
                        CONF_BASE_URL: user_input[CONF_BASE_URL].strip().rstrip("/"),
                        CONF_API_KEY: user_input[CONF_API_KEY].strip(),
                        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(include_scan_interval=True),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Update the API URL or replace a revoked API key."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            user_id, error = await _validate_input(self.hass, user_input)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(user_id)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_BASE_URL: user_input[CONF_BASE_URL].strip().rstrip("/"),
                        CONF_API_KEY: user_input[CONF_API_KEY].strip(),
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(dict(entry.data)),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Replace a revoked API key through the reauthentication flow."""
        del entry_data
        self._reauth_entry_id = self.context["entry_id"]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        """Confirm replacement API credentials."""
        entry = self.hass.config_entries.async_get_entry(self._reauth_entry_id)
        if entry is None:
            return self.async_abort(reason="reauth_entry_not_found")

        errors: dict[str, str] = {}
        if user_input is not None:
            user_id, error = await _validate_input(self.hass, user_input)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(user_id)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_BASE_URL: user_input[CONF_BASE_URL].strip().rstrip("/"),
                        CONF_API_KEY: user_input[CONF_API_KEY].strip(),
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_schema(dict(entry.data)),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow for polling and trip retention."""
        return TrainTrackOptionsFlow(config_entry)


class TrainTrackOptionsFlow(config_entries.OptionsFlow):
    """Allow users to change polling and trip retention after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Save the selected polling interval."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        retention_days = self.config_entry.options.get(
            CONF_ONE_TIME_RETENTION_DAYS, DEFAULT_ONE_TIME_RETENTION_DAYS
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current_interval): _scan_interval_selector(),
                    vol.Required(
                        CONF_ONE_TIME_RETENTION_DAYS, default=retention_days
                    ): _one_time_retention_selector(),
                }
            ),
        )
