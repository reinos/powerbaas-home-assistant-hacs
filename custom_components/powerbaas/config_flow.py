"""Config flow for the Powerbaas integration.

Adding a device starts with a menu asking which kind of Powerbaas device is
being set up. Each device type's own steps live in its own package under
``devices/`` (see P1MeterFlowMixin / BoilerControllerFlowMixin) and are mixed
into this single ConfigFlow class, since Home Assistant only allows one
ConfigFlow per domain.
"""
import logging

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_DEVICE_TYPE, DEVICE_TYPE_P1_METER, DEVICE_TYPE_BOILER_CONTROLLER
from .devices.p1_meter.config_flow import P1MeterFlowMixin, P1MeterOptionsFlow
from .devices.p1_meter.const import P1_MDNS_HOSTNAME
from .devices.boiler_controller.config_flow import (
    BoilerControllerFlowMixin,
    BoilerControllerOptionsFlow,
)
from .devices.boiler_controller.const import BC_HOST_PREFIX

_LOGGER = logging.getLogger(__name__)


class PowerbaasConfigFlow(
    P1MeterFlowMixin,
    BoilerControllerFlowMixin,
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Ask which kind of Powerbaas device is being added."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["p1_meter", "boiler_controller"],
        )

    async def async_step_zeroconf(self, discovery_info):
        """Route Zeroconf discovery to the matching device type's flow.

        Only one class in the MRO can own ``async_step_zeroconf``, so both
        device types' mixins expose private handlers instead
        (``_async_zeroconf_boiler_controller`` / ``_async_zeroconf_p1_meter``)
        and this method dispatches to the right one based on hostname.
        """
        hostname = (discovery_info.hostname or discovery_info.name or "").rstrip(".").split(".")[0].lower()

        if any(hostname.startswith(prefix) for prefix in BC_HOST_PREFIX):
            return await self._async_zeroconf_boiler_controller(discovery_info)
        if hostname == P1_MDNS_HOSTNAME:
            return await self._async_zeroconf_p1_meter(discovery_info)

        return self.async_abort(reason="unsupported_device")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        device_type = config_entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_P1_METER)
        if device_type == DEVICE_TYPE_BOILER_CONTROLLER:
            return BoilerControllerOptionsFlow(config_entry)
        return P1MeterOptionsFlow()
