"""Tests for the Droptimize integration."""

from __future__ import annotations

import json

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.droptimize.const import (
    CONF_REGISTRATION_ID,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)

REGISTRATION_ID = "123456789012345"  # fictief testnummer

BASE_URL = "https://main-bvxea6i-mpaja56t4zhfe.eu-5.platformsh.site"

# Fictieve testdata: sensor id 42, 10000 L put, 175 cm hoog, 60 cm tunnel.
CLAIMS = {
    "sub": 42,
    "id": 42,
    "registrationId": REGISTRATION_ID,
    "postalCode": 2000,
    "street": "Voorbeeldstraat 1",
    "wellType": "oval",
    "wellVolume": 10000,
    "wellHeight": 175,
    "wellTunnelHeight": 60,
    "lidMaterial": "concrete",
    "hasImage": True,
    "role": "sensor",
    "iat": 1795176009,
    "exp": 1795179609,
}

def _fresh_dashboard() -> dict:
    """Dashboard with a reading from a few minutes ago."""
    import datetime

    now = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=5)
    return {
        "sensorId": 42,
        "sensorData": {
            "lastReading": {
                "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "id": 1,
                "distanceRadarInMM": 1383,
                "distanceSonarInMM": 0,
                "batteryV": 3.959,
                "temperature": 23.15,
                "batteryPercent": 80,
                "RSSI": 15,
                "sensorId": 42,
            },
            "volumeDelta7d": -234.28,
        },
        "tips": [],
    }


DASHBOARD = _fresh_dashboard()


def _make_jwt(claims: dict) -> str:
    import base64

    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload = b64(json.dumps(claims).encode())
    return f"{header}.{payload}.signature"


TOKEN = _make_jwt(CLAIMS)


def _mock_api(aioclient_mock, *, token_status: int = 201, dash_status: int = 200):
    """Register the two endpoints the integration calls."""
    aioclient_mock.post(
        f"{BASE_URL}/auth/exchange",
        json={"accessToken": TOKEN},
        status=token_status,
    )
    aioclient_mock.get(
        f"{BASE_URL}/me/dashboard",
        json=DASHBOARD,
        status=dash_status,
    )


async def test_full_setup(hass: HomeAssistant, aioclient_mock) -> None:
    """Test a full setup and the computed values."""
    _mock_api(aioclient_mock)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGISTRATION_ID: REGISTRATION_ID},
        unique_id="42",
        title="Droptimize 123456789012345",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Fill level should be 26% / 2554 L, matching the app and the server.
    assert hass.states.get("sensor.droptimize_123456789012345_fill_level").state == "26"
    assert hass.states.get("sensor.droptimize_123456789012345_water_volume").state == "2554"
    assert hass.states.get("sensor.droptimize_123456789012345_water_depth").state == "138.3"
    assert hass.states.get("sensor.droptimize_123456789012345_battery").state == "80"
    assert hass.states.get("sensor.droptimize_123456789012345_temperature").state == "23.15"
    assert hass.states.get("sensor.droptimize_123456789012345_volume_change_7_days").state == "-234.3"

    # Binary sensors: battery is fine, reading is fresh.
    assert hass.states.get("binary_sensor.droptimize_123456789012345_battery_low").state == "off"
    assert hass.states.get("binary_sensor.droptimize_123456789012345_no_reading_received").state == "off"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_options_scan_interval(hass: HomeAssistant, aioclient_mock) -> None:
    """Test the options flow changes the scan interval."""
    _mock_api(aioclient_mock)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_REGISTRATION_ID: REGISTRATION_ID},
        unique_id="42",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_SCAN_INTERVAL: 3600}
    )
    await hass.async_block_till_done()

    assert entry.options[CONF_SCAN_INTERVAL] == 3600


async def test_config_flow_invalid_registration(hass: HomeAssistant, aioclient_mock) -> None:
    """Test the config flow rejects a bad registration number."""
    aioclient_mock.post(
        f"{BASE_URL}/auth/exchange",
        json={"message": "Invalid sensor token"},
        status=401,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGISTRATION_ID: "000000000000000"},
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_config_flow_success(hass: HomeAssistant, aioclient_mock) -> None:
    """Test the config flow accepts a valid registration number."""
    _mock_api(aioclient_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGISTRATION_ID: REGISTRATION_ID},
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == "Droptimize 123456789012345"
    assert result["data"] == {CONF_REGISTRATION_ID: REGISTRATION_ID}
    assert result["result"].unique_id == "42"


async def test_config_flow_already_configured(hass: HomeAssistant, aioclient_mock) -> None:
    """Test a second setup of the same well aborts."""
    _mock_api(aioclient_mock)

    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    await hass.config_entries.flow.async_configure(
        first["flow_id"], user_input={CONF_REGISTRATION_ID: REGISTRATION_ID}
    )
    await hass.async_block_till_done()

    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    second = await hass.config_entries.flow.async_configure(
        second["flow_id"], user_input={CONF_REGISTRATION_ID: REGISTRATION_ID}
    )
    assert second["type"] == "abort"
    assert second["reason"] == "already_configured"