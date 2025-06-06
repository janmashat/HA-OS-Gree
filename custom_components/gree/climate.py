"""Climate platform for Gree Climate integration."""
import logging
from typing import List, Optional, Any # Dict is no longer needed here

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature, HVACMode,
    FAN_AUTO as DEFAULT_FAN_MODE_STR,
    SWING_OFF as DEFAULT_H_SWING_OFF,
)
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, SUPPORTED_HVAC_MODES_LIST, SUPPORTED_FAN_MODES_LIST,
    AVAILABLE_VERTICAL_SWING_MODES, SUPPORT_FLAGS,
    SUPPORTED_HORIZONTAL_SWING_MODES, GREE_PROPERTY_HORIZONTAL_SWING, GREE_TO_HA_H_SWING_MAP,
    GREE_PROPERTY_POWER, GREE_POWER_OFF, GREE_PROPERTY_MODE,
    GREE_PROPERTY_CURRENT_TEMPERATURE, GREE_PROPERTY_TARGET_TEMPERATURE,
    GREE_PROPERTY_FAN_SPEED, GREE_PROPERTY_VERTICAL_SWING,
    DEFAULT_MIN_TEMP, DEFAULT_MAX_TEMP,
    GREE_MODE_INT_TO_HA_HVACMODE,
    GREE_FANSPEED_INT_TO_HA_FANMODE_STR,
    GREE_TO_HA_VERTICAL_SWING_MAP, VS_OFF,
)
from .coordinator import GreeClimateUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Gree climate entities from a config entry."""
    coordinator: GreeClimateUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GreeClimateEntity(coordinator)])

class GreeClimateEntity(CoordinatorEntity[GreeClimateUpdateCoordinator], ClimateEntity):
    """Representation of a Gree Climate device."""
    _attr_has_entity_name = True
    _attr_name = None 
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1.0
    _attr_supported_features = SUPPORT_FLAGS
    _attr_min_temp = DEFAULT_MIN_TEMP # Use default from const
    _attr_max_temp = DEFAULT_MAX_TEMP # Use default from const

    def __init__(self, coordinator: GreeClimateUpdateCoordinator):
        """Initialize the Gree climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_mac_display}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_mac_display)},
            "name": coordinator.device_name,
            "manufacturer": "Gree",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.coordinator.device is not None

    @property
    def hvac_mode(self) -> HVACMode:
        if not self.coordinator.data or \
           self.coordinator.data.get(GREE_PROPERTY_POWER, GREE_POWER_OFF) == GREE_POWER_OFF:
            return HVACMode.OFF
        gree_mode_val = self.coordinator.data.get(GREE_PROPERTY_MODE)
        return GREE_MODE_INT_TO_HA_HVACMODE.get(gree_mode_val, HVACMode.OFF)

    @property
    def hvac_modes(self) -> List[HVACMode]:
        return SUPPORTED_HVAC_MODES_LIST

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.coordinator.async_set_hvac_mode(hvac_mode)

    @property
    def current_temperature(self) -> Optional[float]:
        if not self.coordinator.data: return None
        temp = self.coordinator.data.get(GREE_PROPERTY_CURRENT_TEMPERATURE)
        return float(temp) if temp is not None else None

    @property
    def target_temperature(self) -> Optional[float]:
        if not self.coordinator.data: return None
        temp = self.coordinator.data.get(GREE_PROPERTY_TARGET_TEMPERATURE)
        return float(temp) if temp is not None else None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self.coordinator.async_set_target_temperature(float(temperature))

    @property
    def fan_mode(self) -> Optional[str]: 
        default_fan_mode = self.fan_modes[0] if self.fan_modes else DEFAULT_FAN_MODE_STR
        if not self.coordinator.data: return default_fan_mode
        gree_fan_speed_val = self.coordinator.data.get(GREE_PROPERTY_FAN_SPEED)
        ha_fan_mode = GREE_FANSPEED_INT_TO_HA_FANMODE_STR.get(gree_fan_speed_val, default_fan_mode)
        return ha_fan_mode if ha_fan_mode in self.fan_modes else default_fan_mode

    @property
    def fan_modes(self) -> List[str]: 
        return SUPPORTED_FAN_MODES_LIST

    async def async_set_fan_mode(self, fan_mode: str) -> None: 
        await self.coordinator.async_set_fan_mode(fan_mode)

    # --- Vertical Swing (Swing Mode) ---
    @property
    def swing_mode(self) -> Optional[str]: 
        default_swing_mode = self.swing_modes[0] if self.swing_modes else VS_OFF
        if not self.coordinator.data: return default_swing_mode
        gree_val = self.coordinator.data.get(GREE_PROPERTY_VERTICAL_SWING)
        ha_swing_mode = GREE_TO_HA_VERTICAL_SWING_MAP.get(gree_val, default_swing_mode)
        return ha_swing_mode if ha_swing_mode in self.swing_modes else default_swing_mode

    @property
    def swing_modes(self) -> List[str]: 
        return AVAILABLE_VERTICAL_SWING_MODES

    async def async_set_swing_mode(self, swing_mode: str) -> None: 
        await self.coordinator.async_set_vertical_swing(swing_mode)

    # --- Horizontal Swing ---
    @property
    def swing_horizontal_mode(self) -> Optional[str]:
        """Return the horizontal swing setting."""
        default_h_swing_mode = self.swing_horizontal_modes[0] if self.swing_horizontal_modes else DEFAULT_H_SWING_OFF
        if not self.coordinator.data: return default_h_swing_mode
        gree_val = self.coordinator.data.get(GREE_PROPERTY_HORIZONTAL_SWING)
        ha_h_swing_mode = GREE_TO_HA_H_SWING_MAP.get(gree_val, default_h_swing_mode)
        return ha_h_swing_mode if ha_h_swing_mode in self.swing_horizontal_modes else default_h_swing_mode

    @property
    def swing_horizontal_modes(self) -> List[str]:
        """Return the list of available horizontal swing modes."""
        return SUPPORTED_HORIZONTAL_SWING_MODES
    
    async def async_set_swing_horizontal_mode(self, swing_mode: str) -> None:
        """Set new target horizontal swing mode."""
        await self.coordinator.async_set_horizontal_swing(swing_mode)
