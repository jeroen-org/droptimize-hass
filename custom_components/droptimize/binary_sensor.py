"""Binary sensor platform for the Droptimize integration."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BATTERY_LOW_PERCENT, DOMAIN, STALE_AFTER
from .coordinator import DroptimizeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: DroptimizeCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            DroptimizeLowBatteryBinarySensor(coordinator, entry),
            DroptimizeStaleBinarySensor(coordinator, entry),
        ]
    )


class DroptimizeBinarySensor(CoordinatorEntity[DroptimizeCoordinator], BinarySensorEntity):
    """Base class for Droptimize binary sensors."""

    _attr_has_entity_name = True
    _attr_translation_key: str

    def __init__(self, coordinator: DroptimizeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{self._attr_translation_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(entry.unique_id))},
            name=entry.title,
            manufacturer="Droptimize",
            model="Regenwaterput-sensor",
        )


class DroptimizeLowBatteryBinarySensor(DroptimizeBinarySensor):
    """Binary sensor indicating a low battery."""

    _attr_translation_key = "low_battery"
    _attr_device_class = BinarySensorDeviceClass.BATTERY
    _attr_icon = "mdi:battery-alert"

    @property
    def is_on(self) -> bool | None:
        """Return True if the battery is low."""
        battery = self.coordinator.data.reading.get("batteryPercent")
        if battery is None:
            return None
        return battery <= BATTERY_LOW_PERCENT


class DroptimizeStaleBinarySensor(DroptimizeBinarySensor):
    """Binary sensor indicating no recent reading was received."""

    _attr_translation_key = "no_reading"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert-circle-outline"

    @property
    def is_on(self) -> bool | None:
        """Return True if the last reading is older than STALE_AFTER."""
        ts = self.coordinator.data.timestamp
        if ts is None:
            return None
        return datetime.now(UTC) - ts > STALE_AFTER