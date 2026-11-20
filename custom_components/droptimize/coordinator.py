"""DataUpdateCoordinator for the Droptimize integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DroptimizeApi, DroptimizeAuthError, DroptimizeConnectionError, DroptimizeError
from .calculations import percent_filled, remaining_liters, water_depth_cm
from .const import (
    BASE_URL,
    CONF_REGISTRATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
)



@dataclass
class DroptimizeData:
    """Data for a single water well."""

    reading: dict[str, Any]
    percent_filled: int
    remaining_liters: float
    water_depth_cm: float
    volume_delta_7d: float | None
    tips: list[dict[str, Any]]
    claims: dict[str, Any]

    @property
    def timestamp(self) -> datetime | None:
        ts = self.reading.get("timestamp")
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None

    @property
    def sensor_id(self) -> int | None:
        return self.reading.get("sensorId") or self.claims.get("id")


class DroptimizeCoordinator(DataUpdateCoordinator[DroptimizeData]):
    """Fetch data from the Droptimize API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.api = DroptimizeApi(
            async_get_clientsession(hass),
            BASE_URL,
            entry.data[CONF_REGISTRATION_ID],
        )

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        if isinstance(scan_interval, (int, float)):
            scan_interval = timedelta(seconds=scan_interval)

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
            config_entry=entry,
        )

    async def _async_update_data(self) -> DroptimizeData:
        try:
            dashboard = await self.api.get_dashboard()
        except DroptimizeAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (DroptimizeConnectionError, DroptimizeError) as err:
            raise UpdateFailed(str(err)) from err

        sensor_data = dashboard.get("sensorData") or {}
        reading = sensor_data.get("lastReading")
        if not reading:
            raise UpdateFailed("Geen metingen beschikbaar (lastReading ontbreekt)")

        claims = self.api.claims
        volume = claims.get("wellVolume", 0)
        height = claims.get("wellHeight", 0)
        tunnel = claims.get("wellTunnelHeight")
        distance_mm = reading.get("distanceRadarInMM", 0)

        return DroptimizeData(
            reading=reading,
            percent_filled=percent_filled(volume, height, tunnel, distance_mm),
            remaining_liters=remaining_liters(volume, height, tunnel, distance_mm),
            water_depth_cm=water_depth_cm(distance_mm),
            volume_delta_7d=sensor_data.get("volumeDelta7d"),
            tips=dashboard.get("tips") or [],
            claims=claims,
        )