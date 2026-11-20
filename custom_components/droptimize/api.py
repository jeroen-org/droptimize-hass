"""Minimal async client for the Droptimize cloud API."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any

import aiohttp

from .const import REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class DroptimizeError(Exception):
    """Base error for this integration."""


class DroptimizeAuthError(DroptimizeError):
    """Raised when the registration id / token is invalid."""


class DroptimizeConnectionError(DroptimizeError):
    """Raised when the API cannot be reached."""


class DroptimizeApi:
    """Async client for the Droptimize cloud API.

    The API returns a short-lived JWT from ``/auth/exchange``. The token is kept
    in memory only and refreshed transparently on expiry or a 401 response.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        registration_id: str,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._registration_id = registration_id
        self._token: str | None = None
        self._token_lock = asyncio.Lock()
        self._claims: dict[str, Any] = {}

    @property
    def claims(self) -> dict[str, Any]:
        """The claims of the current token (well geometry, address, ...)."""
        return self._claims

    async def exchange_token(self, force: bool = False) -> str:
        """Fetch a fresh access token via POST /auth/exchange."""
        async with self._token_lock:
            if self._token and not force:
                return self._token

            data = await self._request(
                "POST",
                "/auth/exchange",
                json_body={"registrationId": self._registration_id},
            )
            token = data.get("accessToken")
            if not token:
                raise DroptimizeAuthError(f"Geen accessToken in antwoord: {data}")

            self._token = token
            self._claims = decode_jwt_claims(token)
            return token

    async def get_dashboard(self) -> dict[str, Any]:
        """GET /me/dashboard — current reading + tips."""
        return await self._request("GET", "/me/dashboard", auth=True)

    async def get_cluster_insights(self) -> dict[str, Any]:
        """GET /me/cluster-insights — neighbourhood statistics."""
        return await self._request("GET", "/me/cluster-insights", auth=True)

    async def post_sensor_insights(
        self,
        start_date: str,
        end_date: str,
        interval: str = "hour",
    ) -> list[dict[str, Any]]:
        """POST /me/sensor-insights — time series of radar distances."""
        return await self._request(
            "POST",
            "/me/sensor-insights",
            json_body={"startDate": start_date, "endDate": end_date, "interval": interval},
            auth=True,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        auth: bool = False,
        _retried: bool = False,
    ) -> Any:
        url = f"{self._base_url}{path}"
        headers: dict[str, str] = {}
        if auth:
            token = await self.exchange_token()
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with self._session.request(
                method,
                url,
                json=json_body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                if resp.status == 401 and auth and not _retried:
                    _LOGGER.debug("401 for %s, forcing token refresh", path)
                    await self.exchange_token(force=True)
                    return await self._request(
                        method, path, json_body=json_body, auth=auth, _retried=True
                    )

                body = await resp.text()
                if resp.status >= 400:
                    if resp.status in (401, 403):
                        raise DroptimizeAuthError(
                            f"{method} {path} -> HTTP {resp.status}: {body}"
                        )
                    raise DroptimizeError(
                        f"{method} {path} -> HTTP {resp.status}: {body}"
                    )
                return json.loads(body) if body else None

        except aiohttp.ClientError as err:
            raise DroptimizeConnectionError(f"{method} {path} -> {err}") from err
        except asyncio.TimeoutError as err:
            raise DroptimizeConnectionError(f"{method} {path} -> timeout") from err


def decode_jwt_claims(token: str) -> dict[str, Any]:
    """Decode the (unverified) payload of a JWT."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except (IndexError, ValueError) as err:
        raise DroptimizeAuthError("Kon JWT niet decoderen") from err