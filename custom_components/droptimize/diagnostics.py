"""Diagnostics support for the Droptimize integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_REGISTRATION_ID, DOMAIN
from .coordinator import DroptimizeCoordinator

TO_REDACT = {CONF_REGISTRATION_ID, "accessToken", "street", "postalCode"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: DroptimizeCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "data": async_redact_data(
            {
                "reading": coordinator.data.reading,
                "percent_filled": coordinator.data.percent_filled,
                "remaining_liters": coordinator.data.remaining_liters,
                "water_depth_cm": coordinator.data.water_depth_cm,
                "volume_delta_7d": coordinator.data.volume_delta_7d,
                "tips": coordinator.data.tips,
                "claims": coordinator.data.claims,
            },
            TO_REDACT,
        ),
    }