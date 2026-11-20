"""Constants for the Droptimize integration."""

from __future__ import annotations

from datetime import timedelta
import logging

DOMAIN = "droptimize"

LOGGER = logging.getLogger(__package__)

# Cloud backend used by the Droptimize app (be.lmr.droptimize).
BASE_URL = "https://main-bvxea6i-mpaja56t4zhfe.eu-5.platformsh.site"

# Requests to the cloud API are slow on first connect; be generous.
REQUEST_TIMEOUT = 20

# Sensor measures roughly once per hour. Polling 4x per hour is a good balance
# between freshness and not hammering an unofficial API.
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)

# Client-side water level calculation, copied from the app (module 5274 of
# index.android.bundle). The API only returns the radar distance; the app derives
# litres and fill percentage from the well geometry.
#
# The app has two hardcoded helpers:
#   getTunnelOffsetConstantCm()    -> Number('52')
#   getDefaultWellTunnelHeightCm() -> Number('60')
#
# TUNNEL_OFFSET_CM (52) is a real hardware constant: the tunnel must be at least
# 52 cm deep so the sensor never ends up underwater (see the app string
# "Diepte van de tunnel moet minimaal 52 cm zijn zodat de sensor niet onder water
# kan komen te staan."). In the formula it is subtracted from the user's tunnel
# height to get the water column above the tunnel.
#
# DEFAULT_TUNNEL_CM (60) is NOT a constant in the same sense: it is only the
# default choice from the tunnel dropdown (options: 52/60/80/100/120/custom).
# The app always uses the user-configured `wellTunnelHeight` (from the JWT
# claims) when present, and only falls back to 60 when that value is missing or
# NaN. We do the same: 60 is used as a last-resort fallback only.
TUNNEL_OFFSET_CM = 52  # getTunnelOffsetConstantCm() — fixed hardware offset
DEFAULT_TUNNEL_CM = 60  # getDefaultWellTunnelHeightCm() — fallback only

# Battery is considered low below this percentage.
BATTERY_LOW_PERCENT = 20

# A reading older than this is considered stale (sensor is offline / broken).
STALE_AFTER = timedelta(hours=3)

CONF_REGISTRATION_ID = "registration_id"
CONF_SCAN_INTERVAL = "scan_interval"