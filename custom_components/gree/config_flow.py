"""Config flow for Gree Climate integration with IP-based MAC discovery."""
import asyncio
import logging
import voluptuous as vol
from ipaddress import ip_address, AddressValueError
from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PORT, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac

_LOGGER = logging.getLogger(__name__)

# Import from the installed greeclimate library structure
try:
    from greeclimate.device import (
        DeviceInfo,
        Device as GreeClimateLibDevice,
        Props as GreePropsEnum
    )
    from greeclimate.discovery import Discovery, Listener
    from greeclimate.exceptions import DeviceTimeoutError, DeviceNotBoundError
except ImportError as e:
    _LOGGER.critical("ConfigFlow: Failed to import from greeclimate: %s. Check library installation.", e)
    GreeClimateLibDevice = None
    DeviceInfo = None
    GreePropsEnum = None
    Discovery = None
    Listener = object # Dummy class to prevent further import errors
    DeviceTimeoutError = type("DeviceTimeoutError", (Exception,), {})
    DeviceNotBoundError = type("DeviceNotBoundError", (Exception,), {})


from .const import DOMAIN, DEFAULT_PORT

IP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)

MANUAL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_MAC): str,
    }
)


class MacFinder(Listener):
    """Listens for a single device response to find its MAC address."""
    def __init__(self, ip_target: str):
        self.found_device_info: DeviceInfo | None = None
        self.found_event = asyncio.Event()
        self.ip_target = ip_target

    async def device_found(self, device_info: DeviceInfo) -> None:
        """Called when a device responds to a scan."""
        _LOGGER.debug("MacFinder: Found device response from %s with info: %s", device_info.ip, device_info)
        # We only care about the device at the IP we targeted
        if device_info.ip == self.ip_target:
            self.found_device_info = device_info
            self.found_event.set()


@config_entries.HANDLERS.register(DOMAIN)
class GreeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gree Climate."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._host: str | None = None
        self._discovered_info: DeviceInfo | None = None

    async def async_step_user(self, user_input: Dict[str, Any] = None) -> config_entries.FlowResult:
        """Handle the initial user step: ask for IP."""
        if not Discovery or not Listener:
            _LOGGER.error("Greeclimate Discovery or Listener class not loaded. Falling back to full manual entry.")
            return await self.async_step_manual()
        
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            return await self.async_step_discover_mac()

        return self.async_show_form(step_id="user", data_schema=IP_SCHEMA)

    async def async_step_discover_mac(self, user_input=None) -> config_entries.FlowResult:
        """Attempt to discover the MAC for the user-provided IP."""
        try:
            target_ip_obj = ip_address(self._host)
        except (AddressValueError, TypeError):
            return self.async_show_form(step_id="user", data_schema=IP_SCHEMA, errors={"base": "invalid_ip"})

        _LOGGER.debug("Attempting unicast discovery for MAC address at %s", self._host)
        discovery = Discovery(timeout=3)
        finder = MacFinder(self._host)
        discovery.add_listener(finder)

        try:
            await discovery.search_on_interface(target_ip_obj)
            await asyncio.wait_for(finder.found_event.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            _LOGGER.warning("No response from %s during MAC discovery. Falling back to full manual entry.", self._host)
            return await self.async_step_manual(user_input={CONF_HOST: self._host})
        except Exception as e:
            _LOGGER.error("Error during targeted MAC discovery: %s", e, exc_info=True)
            return await self.async_step_manual(user_input={CONF_HOST: self._host}, error="discovery_error")

        if finder.found_device_info:
            self._discovered_info = finder.found_device_info
            return await self.async_step_link()
        
        return await self.async_step_manual(user_input={CONF_HOST: self._host})

    async def async_step_link(self, user_input: Dict[str, Any] = None) -> config_entries.FlowResult:
        """Confirm the discovered device and set a name."""
        if user_input is not None:
            # Use the user-provided name, but all other info from discovery
            device_info = self._discovered_info
            device_info.name = user_input[CONF_NAME]

            # Set unique ID before test/create
            formatted_mac = format_mac(device_info.mac)
            await self.async_set_unique_id(formatted_mac)
            self._abort_if_unique_id_configured()

            # Build the final data dict for the config entry
            entry_data = {
                CONF_NAME: device_info.name,
                CONF_HOST: device_info.ip,
                CONF_PORT: device_info.port,
                CONF_MAC: device_info.mac,
            }
            return await self._async_test_and_create_entry(device_info, entry_data)

        # Pre-populate the name field with the discovered name
        discovered_name = self._discovered_info.name if self._discovered_info else self._host
        return self.async_show_form(
            step_id="link",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=discovered_name): str
            }),
            description_placeholders={"host": self._host}
        )
    
    async def async_step_manual(self, user_input: Dict[str, Any] = None, error: str = None) -> config_entries.FlowResult:
        """Handle manual entry of device info as a fallback."""
        errors: Dict[str, str] = {}
        if error: errors["base"] = error

        if user_input is not None and user_input.get(CONF_MAC):
            # If the form is fully filled out, try to create the entry
            mac_raw = user_input[CONF_MAC]
            mac_cleaned_for_lib = mac_raw.replace(":", "").replace("-", "").lower()
            formatted_mac_for_ha = format_mac(mac_raw)
            
            await self.async_set_unique_id(formatted_mac_for_ha)
            self._abort_if_unique_id_configured()

            device_info = DeviceInfo(
                ip=user_input[CONF_HOST],
                port=user_input.get(CONF_PORT, DEFAULT_PORT),
                mac=mac_cleaned_for_lib,
                name=user_input[CONF_NAME]
            )
            return await self._async_test_and_create_entry(user_input, user_input)
        
        # Show the manual form, pre-populating with info from previous steps if available
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=user_input.get(CONF_NAME, "")): str,
                vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_MAC): str,
            }),
            errors=errors
        )
    
    async def _async_test_and_create_entry(self, device_info: DeviceInfo, entry_data: Dict[str, Any]):
        """Shared logic to test connection and create config entry."""
        try:
            test_device = GreeClimateLibDevice(device_info)
            await test_device.bind()
            await test_device.update_state()
            if test_device._properties is not None and test_device.get_property(GreePropsEnum.POWER) is not None:
                return self.async_create_entry(title=device_info.name, data=entry_data)
            else: return self.async_abort(reason="cannot_query_device")
        except DeviceTimeoutError: return self.async_abort(reason="cannot_connect")
        except DeviceNotBoundError: return self.async_abort(reason="device_not_bound")
        except Exception: return self.async_abort(reason="unknown")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return GreeOptionsFlowHandler(config_entry)

class GreeOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Dict[str, Any] = None ) -> config_entries.FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current_update_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        options_schema = vol.Schema(
            {vol.Optional(CONF_UPDATE_INTERVAL, default=current_update_interval): vol.Coerce(int)}
        )
        return self.async_show_form(step_id="init", data_schema=options_schema)

