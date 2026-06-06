"""Constants for Vehicle Service Manager."""

DOMAIN = "vehicle_service"
PLATFORMS = ["sensor", "binary_sensor"]

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "vehicle_service"

# Config flow keys
CONF_MAKE = "make"
CONF_MODEL = "model"
CONF_EZ_DATE = "ez_date"           # Registration Date ISO string
CONF_MILES = "miles"
CONF_PLATE = "plate"
CONF_VIN = "vin"
CONF_HSN = "hsn"
CONF_ENTITY_MILES = "entity_miles"       # optional HA entity for live miles reading
CONF_SERVICES = "services"         # list of selected service IDs
CONF_INTERVALS = "intervals"       # dict: {service_id: {miles?: int, months?: int}}
CONF_INITIAL_HU_DATE = "initial_hu_date"
CONF_INITIAL_HU_MILES = "initial_hu_miles"

# Service IDs
SERVICE_OIL = "oil"
SERVICE_INSPECTION = "inspection"
SERVICE_BRAKE_FLUID = "brake_fluid"
SERVICE_CABIN_FILTER = "cabin_filter"
SERVICE_AIR_FILTER = "air_filter"
SERVICE_SPARK_PLUGS = "spark_plugs"
SERVICE_FUEL_FILTER = "fuel_filter"
SERVICE_GEARBOX = "gearbox"
SERVICE_HALDEX = "haldex"
SERVICE_AC = "ac"
SERVICE_HU = "hu"

ALL_SERVICE_IDS = [
    SERVICE_OIL,
    SERVICE_INSPECTION,
    SERVICE_BRAKE_FLUID,
    SERVICE_CABIN_FILTER,
    SERVICE_AIR_FILTER,
    SERVICE_SPARK_PLUGS,
    SERVICE_FUEL_FILTER,
    SERVICE_GEARBOX,
    SERVICE_HALDEX,
    SERVICE_AC,
    SERVICE_HU,
]

SERVICE_LABELS = {
    SERVICE_OIL: "Oil Change",
    SERVICE_INSPECTION: "Inspection",
    SERVICE_BRAKE_FLUID: "Brake Fluid",
    SERVICE_CABIN_FILTER: "Cabin Filter",
    SERVICE_AIR_FILTER: "Air Filter",
    SERVICE_SPARK_PLUGS: "Spark Plugs",
    SERVICE_FUEL_FILTER: "Fuel Filter",
    SERVICE_GEARBOX: "Transmission Fluid",
    SERVICE_HALDEX: "Haldex Oil",
    SERVICE_AC: "AC Service",
    SERVICE_HU: "Inspection (HU/AU)",
}

# Interval type: "miles", "time", "both"
SERVICE_INTERVAL_TYPE = {
    SERVICE_OIL: "both",
    SERVICE_INSPECTION: "both",
    SERVICE_BRAKE_FLUID: "time",
    SERVICE_CABIN_FILTER: "both",
    SERVICE_AIR_FILTER: "both",
    SERVICE_SPARK_PLUGS: "both",
    SERVICE_FUEL_FILTER: "both",
    SERVICE_GEARBOX: "miles",
    SERVICE_HALDEX: "both",
    SERVICE_AC: "time",
    SERVICE_HU: "time",
}

# Default intervals (converted from metric to imperial)
# km → miles (divide by 1.609344)
DEFAULT_INTERVALS = {
    SERVICE_OIL:          {"miles": 18641, "months": 24},      # 30000 km
    SERVICE_INSPECTION:   {"miles": 18641, "months": 12},      # 30000 km
    SERVICE_BRAKE_FLUID:  {"months": 24},
    SERVICE_CABIN_FILTER: {"miles": 37282, "months": 24},      # 60000 km
    SERVICE_AIR_FILTER:   {"miles": 55923, "months": 72},      # 90000 km
    SERVICE_SPARK_PLUGS:  {"miles": 37282, "months": 48},      # 60000 km
    SERVICE_FUEL_FILTER:  {"miles": 55923, "months": 72},      # 90000 km
    SERVICE_GEARBOX:      {"miles": 37282},                    # 60000 km
    SERVICE_HALDEX:       {"miles": 24854, "months": 36},      # 40000 km
    SERVICE_AC:           {"months": 24},
    SERVICE_HU:           {"months": 24},
}

# HA service call names
HA_SERVICE_ADD_ENTRY = "add_service_entry"
HA_SERVICE_UPDATE_MILES = "update_miles"
HA_SERVICE_ADD_REPAIR = "add_repair"
HA_SERVICE_ADD_TIRE = "add_tire"

# Events
EVENT_SERVICE_DUE = f"{DOMAIN}_service_due"
EVENT_MILES_UPDATED = f"{DOMAIN}_miles_updated"

# Tire wear: 1/32" per 10,000 miles (0.003125" per 10,000 miles)
# Original: 1.5 mm per 10,000 km = 0.059 inches per 10,000 km = 0.00586 inches per 1000 km
# In 32nds: 1.5 mm = 1.89 32nds, so ~0.189 32nds per 10,000 km
TIRE_WEAR_PER_MILE = 0.189 / 10000
TIRE_WARN_SUMMER_32NDS = 3.8   # ~3.0 mm
TIRE_WARN_WINTER_32NDS = 5.1   # ~4.0 mm
TIRE_LEGAL_MIN_32NDS = 2.0     # 1.6 mm
