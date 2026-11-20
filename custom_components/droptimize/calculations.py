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

    Mirrors ``calculateRemainingLiters`` from the app (module 5274):
    1. tunnel_cm = wellTunnelHeight - 52  (offset), or 60 when unknown
    2. water level in cm = radar distance (cm) - tunnel_cm, clipped at 0
    3. water column = well height - water level, clipped to [0, well height]
    4. volume = (well volume / well height) * water column

    ``well_tunnel_height`` is the user-configured tunnel depth (the app's
    dropdown: 52/60/80/100/120/custom). It falls back to 60 only when it is
    missing or not a number — matching ``getDefaultWellTunnelHeightCm``.
    """
    if well_volume <= 0 or well_height <= 0:
        return 0.0

    tunnel_cm = well_tunnel_height
    if tunnel_cm is None or tunnel_cm != tunnel_cm:  # None or NaN
        tunnel_cm = DEFAULT_TUNNEL_CM
    tunnel_cm = max(0.0, float(tunnel_cm) - TUNNEL_OFFSET_CM)

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