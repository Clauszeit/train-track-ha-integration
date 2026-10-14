"""Client for the documented TrainTrack HTTP API."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientSession

from .const import API_CONNECTIONS_PATH, API_SESSION_PATH

REQUEST_TIMEOUT_SECONDS = 20


class TrainTrackApiError(Exception):
    """Base exception for API errors."""


class TrainTrackAuthError(TrainTrackApiError):
    """The configured TrainTrack API key is no longer valid."""


class TrainTrackConnectionError(TrainTrackApiError):
    """The API could not be reached or returned invalid data."""


class TrainTrackApi:
    """Small asynchronous client for a user's TrainTrack account."""

    def __init__(self, session: ClientSession, base_url: str, api_key: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/") + "/"
        self._api_key = api_key

    async def async_get_user(self) -> dict[str, Any]:
        """Validate credentials and return the authenticated user."""
        result = await self._request(API_SESSION_PATH)
        user = result.get("user")
        if not isinstance(user, dict) or not isinstance(user.get("id"), str):
            raise TrainTrackConnectionError("The API response did not contain a user.")
        return user

    async def async_get_connections(self) -> list[dict[str, Any]]:
        """Return the authenticated user's monitored connections."""
        result = await self._request(API_CONNECTIONS_PATH)
        connections = result.get("connections")
        if not isinstance(connections, list) or any(not isinstance(item, dict) for item in connections):
            raise TrainTrackConnectionError("The connections response has an invalid format.")
        return connections

    async def _request(self, path: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS), self._session.get(
                    urljoin(self._base_url, path.lstrip("/")),
                    headers=headers,
                    allow_redirects=False,
                ) as response:
                if response.status in (401, 403):
                    raise TrainTrackAuthError("TrainTrack rejected the configured API key.")
                if response.status < 200 or response.status >= 300:
                    raise TrainTrackConnectionError(
                        f"TrainTrack returned HTTP {response.status}."
                    )
                payload = await response.json(content_type=None)
        except TrainTrackApiError:
            raise
        except (ClientError, TimeoutError, ValueError) as err:
            raise TrainTrackConnectionError("Could not retrieve valid data from TrainTrack.") from err

        if not isinstance(payload, dict):
            raise TrainTrackConnectionError("TrainTrack returned an invalid response.")
        return payload
