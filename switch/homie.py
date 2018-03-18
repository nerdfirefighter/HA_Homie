# IMPORT
import asyncio
import logging

from homeassistant.const import (STATE_UNKNOWN)
from homeassistant.components.switch import (SwitchDevice)
from custom_components.homie import (KEY_HOMIE_ALREADY_DISCOVERED, KEY_HOMIE_ENTITY_NAME, HomieNode)

# TYPINGS
from homeassistant.helpers.typing import (HomeAssistantType, ConfigType)

# CONSTANTS
_LOGGER = logging.getLogger(__name__)
STATE_PROP = 'on'
STATE_ON_VALUE = "true";
STATE_OFF_VALUE = "false";

@asyncio.coroutine
def async_setup_platform(hass: HomeAssistantType, config: ConfigType, async_add_entities, discovery_info=None):
    """Set up the Homie Switch."""
    _LOGGER.info(f"Setting up Homie Switch: {config} - {discovery_info}")

    entity_name = discovery_info[KEY_HOMIE_ENTITY_NAME]
    homie_sensor_node = hass.data[KEY_HOMIE_ALREADY_DISCOVERED][entity_name]
    if homie_sensor_node is None: 
        raise ValueError("Homie Switch faild to recive a Homie Node to bind too")
    if not homie_sensor_node.has_property(STATE_PROP): 
        raise Exception(f"Homie Switch Node doesnt have a {STATE_PROP} property")
    
    async_add_entities([HomieSwitch(entity_name, homie_sensor_node)])


class HomieSwitch(SwitchDevice):
    """Implementation of a Homie Switch."""

    def __init__(self, entity_name: str, homie_sensor_node: HomieNode):
        """Initialize Homie Switch."""
        self._name = entity_name
        self._node = homie_sensor_node
        self._node.device.add_listener(self._on_change)
        self._node.add_listener(self._on_change)
        self._node.get_property(STATE_PROP).add_listener(self._on_change)

    def _on_change(self):
        self.async_schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of the Homie Switch."""
        return self._name

    @property
    def is_on(self):
        """Returns true if the Homie Switch is on."""
        return self._node.get_property(STATE_PROP).state == STATE_ON_VALUE

    @property
    def should_poll(self):
        return False

    async def async_turn_on(self, **kwargs):
        """Turn the device on.

        This method is a coroutine.
        """
        await self._node.get_property(STATE_PROP).async_set_state(STATE_ON_VALUE)

    async def async_turn_off(self, **kwargs):
        """Turn the device off.

        This method is a coroutine.
        """
        await self._node.get_property(STATE_PROP).async_set_state(STATE_OFF_VALUE)
    
    @property
    def available(self):
        """Return if the device is available."""
        return self._node.device.online
