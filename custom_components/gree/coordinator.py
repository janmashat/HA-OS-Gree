"""DataUpdateCoordinator for Gree Climate integration."""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PORT
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

# Import from the installed greeclimate library structure
try:
    from greeclimate.device import (
        Device as GreeClimateLibDevice,
        DeviceInfo,
        Props as GreePropsEnum,
        Mode as GreeModeEnum, 
        FanSpeed as GreeFanSpeedEnum 
    )
    from greeclimate.exceptions import DeviceTimeoutError, DeviceNotBoundError
except ImportError as e:
    _LOGGER.critical("Coordinator: Failed to import from greeclimate.device or greeclimate.exceptions: %s. Check library installation.", e)
    GreeClimateLibDevice = None
    DeviceInfo = None
    GreePropsEnum = None
    GreeModeEnum = None
    GreeFanSpeedEnum = None
    DeviceTimeoutError = type("DeviceTimeoutError", (Exception,), {})
    DeviceNotBoundError = type("DeviceNotBoundError", (Exception,), {})

from .const import (
    DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL,
    GREE_PROPERTY_POWER, GREE_PROPERTY_MODE, GREE_PROPERTY_TARGET_TEMPERATURE,
    GREE_PROPERTY_CURRENT_TEMPERATURE, GREE_PROPERTY_FAN_SPEED,
    GREE_PROPERTY_HORIZONTAL_SWING, GREE_PROPERTY_VERTICAL_SWING,
    GREE_PROPERTY_LIGHT, GREE_PROPERTY_QUIET,
    # Import the new horizontal swing map
    HA_H_SWING_TO_GREE_MAP, 
    HA_TO_GREE_VERTICAL_SWING_MAP,
    HA_HVACMODE_TO_GREE_MODE_INT, HA_FANMODE_STR_TO_GREE_FANSPEED_INT,
    HVACMode, GREE_POWER_ON, GREE_POWER_OFF,
)

class GreeClimateUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Manages fetching data and sending commands to the Gree device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the data update coordinator."""
        self.hass = hass
        self.entry = entry
        self._host: str = entry.data[CONF_HOST]
        self._port: int = entry.data[CONF_PORT]
        self._mac_cleaned: str = entry.data[CONF_MAC].replace(":", "").replace("-", "").lower()
        self.device_name: str = entry.title
        self.device_mac_display: str = entry.data[CONF_MAC].upper()

        if not all([GreeClimateLibDevice, DeviceInfo, GreePropsEnum, GreeModeEnum, GreeFanSpeedEnum]):
            _LOGGER.error("Greeclimate library components not fully loaded for %s. Device control will not be available.", self.device_name)
            self.device: Optional[GreeClimateLibDevice] = None
        else:
            device_info_obj = DeviceInfo(ip=self._host, port=self._port, mac=self._mac_cleaned, name=self.device_name)
            self.device: Optional[GreeClimateLibDevice] = GreeClimateLibDevice(device_info_obj)

        self._lock = asyncio.Lock()
        self._is_bound = False

        update_interval_seconds = entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN} ({self.device_name})",
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        _LOGGER.info("Gree Coordinator for %s initialized (interval: %ss)", self.device_name, update_interval_seconds)

    async def _ensure_bound(self):
        """Ensure device is bound. Call before operations that require a device key."""
        if self.device and not self.device.device_key and not self._is_bound: 
            try:
                _LOGGER.debug("%s: Attempting to bind.", self.device_name)
                await self.device.bind()
                self._is_bound = True
                _LOGGER.info("%s: Successfully bound.", self.device_name)
            except (DeviceTimeoutError, DeviceNotBoundError) as e:
                _LOGGER.warning("%s: Binding failed: %s", self.device_name, e)
                self._is_bound = False 
                raise 
            except Exception as e:
                _LOGGER.error("%s: Unexpected error during bind: %s", self.device_name, e, exc_info=True)
                self._is_bound = False
                raise

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch the latest data from the Gree device."""
        if not self.device:
            _LOGGER.debug("%s: Device object not initialized in coordinator, skipping update.", self.device_name)
            raise UpdateFailed(f"Device object not initialized for {self.device_name}")

        async with self._lock:
            try:
                await self._ensure_bound()
                _LOGGER.debug("%s: Calling library's update_state()", self.device_name)
                await self.device.update_state()
                
                if self.device._properties is not None and isinstance(self.device._properties, dict):
                    # Start with a copy of the raw properties from the library
                    ha_state_dict = self.device._properties.copy()
                    
                    # Explicitly get the processed current_temperature from the library's property
                    # This allows the library to apply its offset logic.
                    # The library's device.current_temperature property returns an int.
                    library_current_temp = self.device.current_temperature 
                    if library_current_temp is not None:
                        _LOGGER.debug(
                            "%s: Library processed current_temperature: %s (Raw TemSen from _properties was: %s)",
                            self.device_name,
                            library_current_temp,
                            self.device._properties.get(GreePropsEnum.TEMP_SENSOR.value) # Get raw for logging
                        )
                        ha_state_dict[GREE_PROPERTY_CURRENT_TEMPERATURE] = float(library_current_temp)
                    else:
                        # If library_current_temp is None, keep the raw TemSen or let it be absent
                        _LOGGER.warning("%s: Library device.current_temperature returned None. Using raw TemSen if available.", self.device_name)
                        # Ensure GREE_PROPERTY_CURRENT_TEMPERATURE key exists if raw value was there
                        if GreePropsEnum.TEMP_SENSOR.value in ha_state_dict:
                             ha_state_dict[GREE_PROPERTY_CURRENT_TEMPERATURE] = ha_state_dict[GreePropsEnum.TEMP_SENSOR.value]


                    _LOGGER.debug("%s: State after update (processed): %s", self.device_name, ha_state_dict)
                    
                    if not ha_state_dict and len(self.device._properties) > 0:
                         _LOGGER.warning("%s: ha_state_dict became empty unexpectedly. Library _properties: %s", self.device_name, self.device._properties)
                    elif not ha_state_dict: 
                         _LOGGER.info("%s: Library _properties was an empty dictionary. Device might be off or in a minimal reporting state.", self.device_name)
                    return ha_state_dict
                else:
                    _LOGGER.warning("%s: Library self.device._properties is None or not a dict after update_state(). Type: %s", 
                                    self.device_name, type(self.device._properties))
                    return {} 
            except (DeviceTimeoutError, DeviceNotBoundError) as e:
                self._is_bound = False 
                _LOGGER.warning("%s: Update failed (timeout/not bound): %s", self.device_name, e)
                raise UpdateFailed(f"Device {self.device_name} communication error: {e}") from e
            except Exception as e:
                _LOGGER.error("%s: Unexpected error during state update: %s", self.device_name, e, exc_info=True)
                raise UpdateFailed(f"Unexpected error updating {self.device_name}: {e}") from e

    async def _execute_command_and_refresh(self, command_coro_func, optimistic_props: Optional[Dict[str, Any]] = None):
        """Helper to execute a device command, push, optimistically update, and refresh."""
        if not self.device:
            _LOGGER.error("%s: Device not initialized, cannot execute command.", self.device_name)
            return

        async with self._lock:
            try:
                await self._ensure_bound()
                await command_coro_func() 
                await self.device.push_state_update() 
                _LOGGER.debug("%s: Command executed and pushed successfully.", self.device_name)
                
                if optimistic_props and self.data is not None:
                    self.data.update(optimistic_props)
                    _LOGGER.debug("%s: Optimistically updated self.data: %s", self.device_name, optimistic_props)
                    self.async_update_listeners() 

            except (DeviceTimeoutError, DeviceNotBoundError) as e:
                self._is_bound = False
                _LOGGER.error("%s: Command failed (timeout/not bound): %s", self.device_name, e)
            except Exception as e:
                _LOGGER.error("%s: Unexpected error during command: %s", self.device_name, e, exc_info=True)
        
        await self.async_request_refresh()


    async def async_set_power(self, turn_on: bool) -> None:
        async def command(): 
            if self.device: self.device.power = turn_on
        await self._execute_command_and_refresh(
            command, 
            optimistic_props={GREE_PROPERTY_POWER: GREE_POWER_ON if turn_on else GREE_POWER_OFF}
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.async_set_power(False)
        else:
            is_currently_on = self.data.get(GREE_PROPERTY_POWER, GREE_POWER_OFF) == GREE_POWER_ON if self.data else False
            if not is_currently_on:
                await self.async_set_power(True) 
                await asyncio.sleep(0.5) 
            
            if hvac_mode in HA_HVACMODE_TO_GREE_MODE_INT:
                gree_mode_val = HA_HVACMODE_TO_GREE_MODE_INT[hvac_mode]
                async def command(): 
                    if self.device : self.device.mode = gree_mode_val
                await self._execute_command_and_refresh(
                    command,
                    optimistic_props={GREE_PROPERTY_MODE: gree_mode_val, GREE_PROPERTY_POWER: GREE_POWER_ON}
                )
            else: _LOGGER.warning("%s: Unsupported HVACMode: %s", self.device_name, hvac_mode)

    async def async_set_target_temperature(self, temperature: float) -> None:
        temp_int = int(temperature)
        async def command(): 
            if self.device: self.device.target_temperature = temp_int
        await self._execute_command_and_refresh(
            command,
            optimistic_props={GREE_PROPERTY_TARGET_TEMPERATURE: temp_int}
        )

    async def async_set_fan_mode(self, fan_mode_str: str) -> None:
        if fan_mode_str in HA_FANMODE_STR_TO_GREE_FANSPEED_INT:
            gree_fan_speed_val = HA_FANMODE_STR_TO_GREE_FANSPEED_INT[fan_mode_str]
            async def command(): 
                if self.device: self.device.fan_speed = gree_fan_speed_val
            await self._execute_command_and_refresh(
                command,
                optimistic_props={GREE_PROPERTY_FAN_SPEED: gree_fan_speed_val}
            )
        else: _LOGGER.warning("%s: Unsupported fan mode string: %s", self.device_name, fan_mode_str)

    async def async_set_horizontal_swing(self, swing_mode_str: str) -> None:
        if swing_mode_str in HA_H_SWING_TO_GREE_MAP and GreePropsEnum is not None:
            gree_val = HA_H_SWING_TO_GREE_MAP[swing_mode_str]
            async def command(): 
                if self.device: self.device.set_property(GreePropsEnum.SWING_HORIZ, gree_val)
            await self._execute_command_and_refresh(
                command,
                optimistic_props={GREE_PROPERTY_HORIZONTAL_SWING: gree_val}
            )
        else: _LOGGER.warning("%s: Unsupported horizontal swing mode: %s", self.device_name, swing_mode_str)


    async def async_set_vertical_swing(self, swing_mode_str: str) -> None:
        if swing_mode_str in HA_TO_GREE_VERTICAL_SWING_MAP and GreePropsEnum is not None:
            gree_val = HA_TO_GREE_VERTICAL_SWING_MAP[swing_mode_str]
            async def command(): 
                if self.device: self.device.set_property(GreePropsEnum.SWING_VERT, gree_val)
            await self._execute_command_and_refresh(
                command,
                optimistic_props={GREE_PROPERTY_VERTICAL_SWING: gree_val}
            )
        else: _LOGGER.warning("%s: Unsupp. vert. swing mode: %s", self.device_name, swing_mode_str)

    async def async_set_light(self, turn_on: bool) -> None:
        async def command(): 
            if self.device: self.device.light = turn_on
        await self._execute_command_and_refresh(
            command,
            optimistic_props={GREE_PROPERTY_LIGHT: GREE_POWER_ON if turn_on else GREE_POWER_OFF}
        )

    async def async_set_quiet_mode(self, turn_on: bool) -> None:
        async def command(): 
            if self.device: self.device.quiet = turn_on
        await self._execute_command_and_refresh(
            command,
            optimistic_props={GREE_PROPERTY_QUIET: GREE_POWER_ON if turn_on else GREE_POWER_OFF}
        )
