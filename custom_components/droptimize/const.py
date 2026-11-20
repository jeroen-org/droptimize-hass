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

# Client-side water level calculation, copied from the app (module 5274/5275 of
# index.android.bundle). The API only returns the radar distance; the app derives
# litres and fill percentage from the well geometry.
#
# If the app changes these values in a future release, update them here.
TUNNEL_OFFSET_CM = 52  # getTunnelOffsetConstantCm()
DEFAULT_TUNNEL_CM = 60  # getDefaultWellTunnelHeightCm()

# Battery is considered low below this percentage.
BATTERY_LOW_PERCENT = 20

# A reading older than this is considered stale (sensor is offline / broken).
STALE_AFTER = timedelta(hours=3)

CONF_REGISTRATION_ID = "registration_id"
CONF_SCAN_INTERVAL = "scan_interval"