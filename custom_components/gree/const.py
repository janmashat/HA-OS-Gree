"""Constants for the Gree Climate integration."""
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
    # Fan modes are string constants
    FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH,
    # Standard HA horizontal swing mode strings
    SWING_ON, SWING_OFF, SWING_HORIZONTAL, SWING_VERTICAL,
    SWING_BOTH
)
from homeassistant.const import UnitOfTemperature

DOMAIN = "gree"

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_MAC = "mac"
CONF_NAME = "name"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_PORT = 7000
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_MIN_TEMP = 16.0
DEFAULT_MAX_TEMP = 30.0

# Gree Property String Names
GREE_PROPERTY_POWER = "Pow"
GREE_PROPERTY_MODE = "Mod"
GREE_PROPERTY_TARGET_TEMPERATURE = "SetTem"
GREE_PROPERTY_CURRENT_TEMPERATURE = "TemSen"
GREE_PROPERTY_FAN_SPEED = "WdSpd"
GREE_PROPERTY_LIGHT = "Lig"
GREE_PROPERTY_QUIET = "Quiet"
GREE_PROPERTY_HORIZONTAL_SWING = "SwingLfRig" 
GREE_PROPERTY_VERTICAL_SWING = "SwUpDn"       

# --- Horizontal Swing (for ClimateEntity) ---
# Mapping from standard HA horizontal swing mode strings to our Gree values
HA_H_SWING_TO_GREE_MAP = {
    SWING_OFF: 0, # Or your preferred fixed position for "Off"
    "Full Swing": 1, # Using a descriptive name for the full range
    "Far Left": 2,
    "Left": 3,
    "Center": 4,
    "Right": 5,
    "Far Right": 6
}
GREE_TO_HA_H_SWING_MAP = {v: k for k, v in HA_H_SWING_TO_GREE_MAP.items()}
# This is the list of options that will appear in the UI dropdown
SUPPORTED_HORIZONTAL_SWING_MODES = list(HA_H_SWING_TO_GREE_MAP.keys())

# --- Vertical Swing (for ClimateEntity) ---
VS_OFF = "Off"
VS_FULL = "Full Vertical"
VS_HIGHEST = "Highest"
VS_HIGH = "High"
VS_MIDDLE = "Middle (V)"
VS_LOW = "Low"
VS_LOWEST = "Lowest"
AVAILABLE_VERTICAL_SWING_MODES = [
    VS_OFF, VS_FULL, VS_HIGHEST, VS_HIGH, VS_MIDDLE, VS_LOW, VS_LOWEST,
]
HA_TO_GREE_VERTICAL_SWING_MAP = { 
    VS_OFF: 0, VS_FULL: 1, VS_HIGHEST: 2, VS_HIGH: 3,
    VS_MIDDLE: 4, VS_LOW: 5, VS_LOWEST: 6,
}
GREE_TO_HA_VERTICAL_SWING_MAP = {v: k for k, v in HA_TO_GREE_VERTICAL_SWING_MAP.items()}

# --- HVAC Modes ---
GREE_MODE_INT_TO_HA_HVACMODE = { 
    0: HVACMode.AUTO, 1: HVACMode.COOL, 2: HVACMode.DRY,
    3: HVACMode.FAN_ONLY, 4: HVACMode.HEAT,
}
HA_HVACMODE_TO_GREE_MODE_INT = {v: k for k, v in GREE_MODE_INT_TO_HA_HVACMODE.items()}
SUPPORTED_HVAC_MODES_LIST = [HVACMode.OFF] + list(HA_HVACMODE_TO_GREE_MODE_INT.keys())

# --- Fan Modes ---
GREE_FANSPEED_INT_TO_HA_FANMODE_STR = { 
    0: FAN_AUTO, 1: FAN_LOW, 2: FAN_LOW,   
    3: FAN_MEDIUM, 4: FAN_HIGH, 5: FAN_HIGH,
}
HA_FANMODE_STR_TO_GREE_FANSPEED_INT = { 
    FAN_AUTO: 0, FAN_LOW: 1, FAN_MEDIUM: 3, FAN_HIGH: 5,
}
SUPPORTED_FAN_MODES_LIST = list(HA_FANMODE_STR_TO_GREE_FANSPEED_INT.keys())

# --- Switch Types ---
SWITCH_TYPE_LIGHT = "light"
SWITCH_TYPE_QUIET = "quiet"

# --- Supported Features (using ClimateEntityFeature Enum) ---
SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.SWING_MODE           # For Vertical Swing
    | ClimateEntityFeature.SWING_HORIZONTAL_MODE # For Horizontal Swing
)

TEMP_CELSIUS = UnitOfTemperature.CELSIUS
GREE_POWER_OFF = 0
GREE_POWER_ON = 1
