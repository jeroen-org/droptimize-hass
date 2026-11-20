"""Sensor platform for the Droptimize integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DroptimizeCoordinator, DroptimizeData


@dataclass(frozen=True, kw_only=True)
class DroptimizeSensorEntityDescription(SensorEntityDescription):
    """Describes a Droptimize sensor."""

    value_fn: Callable[[DroptimizeData], StateType]


SENSORS: tuple[DroptimizeSensorEntityDescription, ...] = (
    DroptimizeSensorEntityDescription(
        key="percent_filled",
        translation_key="percent_filled",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-percent",
        value_fn=lambda d: d.percent_filled,
    ),
    DroptimizeSensorEntityDescription(
        key="remaining_liters",
        translation_key="remaining_liters",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:water",
        value_fn=lambda d: round(d.remaining_liters),
    ),
    DroptimizeSensorEntityDescription(
        key="water_depth",
        translation_key="water_depth",
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-expand-vertical",
        value_fn=lambda d: d.water_depth_cm,
    ),
    DroptimizeSensorEntityDescription(
        key="battery",
        translation_key="battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.reading.get("batteryPercent"),
    ),
    DroptimizeSensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.reading.get("batteryV"),
    ),
    DroptimizeSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.reading.get("temperature"),
    ),
    DroptimizeSensorEntityDescription(
        key="last_reading",
        translation_key="last_reading",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.timestamp,
    ),
    DroptimizeSensorEntityDescription(
        key="volume_delta_7d",
        translation_key="volume_delta_7d",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:trending-down",
        value_fn=lambda d: round(d.volume_delta_7d, 1) if d.volume_delta_7d is not None else None,
    ),
    DroptimizeSensorEntityDescription(
        key="radar_distance",
        translation_key="radar_distance",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.reading.get("distanceRadarInMM"),
    ),
    DroptimizeSensorEntityDescription(
        key="rssi",
        translation_key="rssi",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:signal",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.reading.get("RSSI"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: DroptimizeCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        DroptimizeSensor(coordinator, entry, description) for description in SENSORS
    )


class DroptimizeSensor(CoordinatorEntity[DroptimizeCoordinator], SensorEntity):
    """Representation of a Droptimize sensor."""

    entity_description: DroptimizeSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DroptimizeCoordinator,
        entry: ConfigEntry,
        description: DroptimizeSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(entry.unique_id))},
            name=entry.title,
            manufacturer="Droptimize",
            model="Regenwaterput-sensor",
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)