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


def test_default_tunnel_when_nan():
    """A NaN tunnel height also falls back to the default (60 cm)."""
    assert remaining_liters(VOL, HEIGHT, float("nan"), 1383) == remaining_liters(
        VOL, HEIGHT, 60, 1383
    )


def test_configured_tunnel_changes_result():
    """A user-configured tunnel height is used, not the 60 cm default.

    The tunnel dropdown in the app offers 52/60/80/100/120/custom. A deeper
    tunnel (100 cm) leaves more room for water, so the fill percentage rises.
    """
    shallow = percent_filled(VOL, HEIGHT, 60, 1383)
    deep = percent_filled(VOL, HEIGHT, 100, 1383)
    assert deep > shallow
    assert (shallow, deep) == (26, 48)


def test_custom_tunnel_height():
    """A custom (non-dropdown) tunnel height is honoured too."""
    # 80 cm tunnel, same reading -> between the 60 and 100 cases
    assert percent_filled(VOL, HEIGHT, 80, 1383) == 37


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