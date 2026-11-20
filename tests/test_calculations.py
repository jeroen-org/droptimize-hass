"""Pure unit tests for the Droptimize calculations (no Home Assistant needed)."""

from __future__ import annotations

import pytest

from custom_components.droptimize.calculations import (
    percent_filled,
    remaining_liters,
    water_depth_cm,
)

# Real test sensor: wellVolume=10000, wellHeight=175, wellTunnelHeight=60
VOL = 10000
HEIGHT = 175
TUNNEL = 60


def test_known_reading_1383mm():
    """1383 mm -> 26% / 2554 L, matching the app and server."""
    assert percent_filled(VOL, HEIGHT, TUNNEL, 1383) == 26
    assert round(remaining_liters(VOL, HEIGHT, TUNNEL, 1383)) == 2554


def test_water_depth():
    """Radar distance in mm converts to cm."""
    assert water_depth_cm(1383) == 138.3


def test_empty_well():
    """An empty well returns zero."""
    assert percent_filled(VOL, HEIGHT, TUNNEL, 2000) == 0
    assert remaining_liters(VOL, HEIGHT, TUNNEL, 2000) == 0.0


def test_full_well():
    """A full well returns 100% / full volume."""
    # distance 0 -> water at the tunnel top -> full well
    assert percent_filled(VOL, HEIGHT, TUNNEL, 0) == 100
    assert round(remaining_liters(VOL, HEIGHT, TUNNEL, 0)) == VOL


def test_zero_volume():
    """A zero-volume well returns zero without dividing by zero."""
    assert percent_filled(0, HEIGHT, TUNNEL, 1383) == 0
    assert remaining_liters(0, HEIGHT, TUNNEL, 1383) == 0.0


def test_default_tunnel_when_none():
    """Missing tunnel height falls back to the default (60 cm)."""
    assert remaining_liters(VOL, HEIGHT, None, 1383) == remaining_liters(
        VOL, HEIGHT, 60, 1383
    )


@pytest.mark.parametrize(
    ("distance", "expected_pct"),
    [
        (0, 100),
        (1000, 47),
        (1383, 26),
        (2000, 0),
    ],
)
def test_monotonic_fill(distance, expected_pct):
    """Fill percentage decreases monotonically as the radar distance grows."""
    assert percent_filled(VOL, HEIGHT, TUNNEL, distance) == expected_pct