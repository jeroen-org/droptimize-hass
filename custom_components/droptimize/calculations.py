"""Water level calculations, mirroring the Droptimize app exactly."""

from __future__ import annotations

from .const import DEFAULT_TUNNEL_CM, TUNNEL_OFFSET_CM


def remaining_liters(
    well_volume: float,
    well_height: float,
    well_tunnel_height: float | None,
    distance_mm: float,
) -> float:
    """Return the remaining water volume in litres.

    Mirrors ``calculateRemainingLiters`` from the app:
    1. radar distance (mm) -> water level in cm below the tunnel
    2. water column height = well height - water level
    3. volume = (well volume / well height) * water column
    """
    if well_volume <= 0 or well_height <= 0:
        return 0.0

    tunnel_cm = DEFAULT_TUNNEL_CM if well_tunnel_height is None else well_tunnel_height
    tunnel_cm = max(0.0, tunnel_cm - TUNNEL_OFFSET_CM)

    water_level_cm = max(0.0, distance_mm / 10.0 - tunnel_cm)
    water_column_cm = min(max(well_height - water_level_cm, 0.0), well_height)

    return max(0.0, round((well_volume * 1000.0 / well_height) * water_column_cm / 1000.0, 5))


def percent_filled(
    well_volume: float,
    well_height: float,
    well_tunnel_height: float | None,
    distance_mm: float,
) -> int:
    """Return the fill percentage (0-100), mirroring ``calculateWaterLevelPercentage``."""
    if well_volume <= 0:
        return 0

    liters = remaining_liters(well_volume, well_height, well_tunnel_height, distance_mm)
    return round(liters / well_volume * 100)


def water_depth_cm(distance_mm: float) -> float:
    """Radar distance converted to centimetres below the sensor."""
    return round(distance_mm / 10.0, 1)