"""Sensor platform for Vehicle Service Manager."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SERVICE_LABELS,
    TIRE_WEAR_PER_MILE, TIRE_WARN_SUMMER_32NDS, TIRE_WARN_WINTER_32NDS, TIRE_LEGAL_MIN_32NDS,
)
from .store import get_store, VehicleServiceStore

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for each selected service point."""
    store = get_store(hass)
    await store.async_load()
    vehicle_id: str = hass.data[DOMAIN][entry.entry_id]["vehicle_id"]
    vehicle = store.get_vehicle(vehicle_id)

    if vehicle is None:
        return

    entities: list[SensorEntity] = []

    for svc_id in vehicle.get("services", []):
        entities.append(ServiceStatusSensor(hass, store, vehicle_id, svc_id, entry))

    entities.append(MilesSensor(hass, store, vehicle_id, entry))

    for pos in ["vl", "vr", "hl", "hr"]:
        entities.append(TireDepthSensor(hass, store, vehicle_id, pos, entry))

    async_add_entities(entities, update_before_add=True)

    # Refresh all sensors when data changes via WebSocket
    async def _on_data_changed(event) -> None:
        if event.data.get("vehicle_id") == vehicle_id:
            for entity in entities:
                entity.async_schedule_update_ha_state(force_refresh=True)

    hass.bus.async_listen(f"{DOMAIN}_service_entry_added", _on_data_changed)
    hass.bus.async_listen(f"{DOMAIN}_miles_updated",          _on_data_changed)


# ── Helpers ───────────────────────────────────────────────────────────

def _months_since(iso_date: str) -> float:
    """Return months elapsed since an ISO date string."""
    try:
        d = date.fromisoformat(iso_date)
    except (ValueError, TypeError):
        return 0.0
    return (date.today() - d).days / 30.44


def _calc_pct(vehicle: dict, svc_id: str) -> tuple[float, float | None, float | None]:
    """Return (pct, miles_left, months_left) — worst of miles and time axes."""
    last = vehicle.get("lastService", {}).get(svc_id, {})
    intv = vehicle.get("intervals", {}).get(svc_id, {})
    ez_date: str | None = vehicle.get("ezDate")
    current_miles: int = vehicle.get("miles", 0)

    miles_pct: float | None = None
    miles_left: float | None = None
    time_pct: float | None = None
    months_left: float | None = None

    if intv.get("miles"):
        base_miles = last.get("miles") or 0
        driven = current_miles - base_miles
        miles_pct = min(100.0, round(driven / intv["miles"] * 100, 1))
        miles_left = max(0.0, intv["miles"] - driven)

    if intv.get("months"):
        base_date = last.get("date") or ez_date
        if base_date:
            ms = _months_since(base_date)
            time_pct = min(100.0, round(ms / intv["months"] * 100, 1))
            months_left = max(0.0, round(intv["months"] - ms, 1))
        else:
            time_pct = 0.0
            months_left = float(intv["months"])

    pct = (
        max(p for p in [miles_pct, time_pct] if p is not None)
        if (miles_pct is not None or time_pct is not None)
        else 0.0
    )
    return pct, miles_left, months_left


def _status_from_pct(pct: float) -> str:
    if pct >= 100:
        return "overdue"
    if pct >= 90:
        return "due"
    if pct >= 70:
        return "soon"
    if pct >= 50:
        return "watch"
    return "ok"


def _device_info(store: VehicleServiceStore, vehicle_id: str) -> DeviceInfo:
    vehicle = store.get_vehicle(vehicle_id)
    make = vehicle.get("make", "") if vehicle else ""
    model = vehicle.get("model", "") if vehicle else ""
    return DeviceInfo(
        identifiers={(DOMAIN, vehicle_id)},
        name=f"{make} {model}",
        manufacturer=make,
        model=model,
    )


# ── Service status sensor ─────────────────────────────────────────────────────

class ServiceStatusSensor(SensorEntity):
    """Sensor reporting status/percentage for one service point."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:car-wrench"

    def __init__(
        self,
        hass: HomeAssistant,
        store: VehicleServiceStore,
        vehicle_id: str,
        svc_id: str,
        entry: ConfigEntry,
    ) -> None:
        self._store = store
        self._vehicle_id = vehicle_id
        self._svc_id = svc_id
        self._attr_unique_id = f"{vehicle_id}_{svc_id}_status"
        self._attr_name = SERVICE_LABELS.get(svc_id, svc_id)
        self._attr_native_value: str = "ok"
        self._extra: dict[str, Any] = {}

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._store, self._vehicle_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._extra

    async def async_update(self) -> None:
        """Update state — synchronous store read wrapped in async def."""
        vehicle = self._store.get_vehicle(self._vehicle_id)
        if vehicle is None:
            return

        pct, miles_left, months_left = _calc_pct(vehicle, self._svc_id)
        status = _status_from_pct(pct)
        self._attr_native_value = status

        last = vehicle.get("lastService", {}).get(self._svc_id, {})
        intv = vehicle.get("intervals", {}).get(self._svc_id, {})

        self._extra = {
            "vehicle_id": self._vehicle_id,
            "service_id": self._svc_id,
            "percentage": pct,
            "status": status,
            "last_service_date": last.get("date"),
            "last_service_miles": last.get("miles"),
            "miles_left": miles_left,
            "months_left": months_left,
            "interval_miles": intv.get("miles"),
            "interval_months": intv.get("months"),
        }


# ── Miles sensor ───────────────────────────────────────────────────────

class MilesSensor(SensorEntity):
    """Sensor showing current miles reading for a vehicle."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = "mi"
    _attr_icon = "mdi:gauge"

    def __init__(
        self,
        hass: HomeAssistant,
        store: VehicleServiceStore,
        vehicle_id: str,
        entry: ConfigEntry,
    ) -> None:
        self._store = store
        self._vehicle_id = vehicle_id
        self._attr_unique_id = f"{vehicle_id}_miles"
        self._attr_name = "Odometer"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._store, self._vehicle_id)

    async def async_update(self) -> None:
        vehicle = self._store.get_vehicle(self._vehicle_id)
        if vehicle:
            self._attr_native_value = vehicle.get("miles", 0)


# ── Tire depth sensor ────────────────────────────────────────────────────────

class TireDepthSensor(SensorEntity):
    """Sensor showing projected tread depth (32nds) for one wheel position."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "32nds"
    _attr_icon = "mdi:tire"

    POS_LABELS = {
        "vl": "Tire FL",
        "vr": "Tire FR",
        "hl": "Tire RL",
        "hr": "Tire RR",
    }

    def __init__(
        self,
        hass: HomeAssistant,
        store: VehicleServiceStore,
        vehicle_id: str,
        position: str,
        entry: ConfigEntry,
    ) -> None:
        self._store = store
        self._vehicle_id = vehicle_id
        self._position = position
        self._attr_unique_id = f"{vehicle_id}_tire_{position}"
        self._attr_name = self.POS_LABELS.get(position, position.upper())
        self._extra: dict[str, Any] = {}

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._store, self._vehicle_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._extra

    async def async_update(self) -> None:
        vehicle = self._store.get_vehicle(self._vehicle_id)
        if vehicle is None:
            return

        tires = vehicle.get("tires", [])
        if not tires:
            self._attr_native_value = None
            return

        latest = tires[-1]
        orig = float(latest.get(self._position) or 0)
        if not orig:
            self._attr_native_value = None
            return

        mounted_miles = int(latest.get("miles") or 0)
        current_miles = vehicle.get("miles", 0)
        driven = max(0, current_miles - mounted_miles)
        worn = round(max(0.0, orig - driven * TIRE_WEAR_PER_MILE), 2)

        tire_type = latest.get("type", "summer")
        warn_32nds = TIRE_WARN_WINTER_32NDS if tire_type in ("winter", "allseason") else TIRE_WARN_SUMMER_32NDS

        if worn <= TIRE_LEGAL_MIN_32NDS:
            status = "critical"
        elif worn <= warn_32nds:
            status = "warning"
        else:
            status = "ok"

        self._attr_native_value = worn
        self._extra = {
            "original_depth_32nds": orig,
            "mounted_miles": mounted_miles,
            "driven_miles": driven,
            "status": status,
            "warn_limit_32nds": warn_32nds,
            "legal_min_32nds": TIRE_LEGAL_MIN_32NDS,
            "tire_type": tire_type,
            "brand": latest.get("brand", ""),
            "size": f"{latest.get('width','')}/{latest.get('ratio','')} R{latest.get('rim','')}",
            "dot": latest.get("dot", ""),
        }
