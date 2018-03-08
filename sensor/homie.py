# IMPORT
import asyncio
import logging

from homeassistant.const import (STATE_UNKNOWN)
from homeassistant.helpers.entity import (Entity)
from custom_components.homie import (KEY_HOMIE_ALREADY_DISCOVERED, KEY_HOMIE_ENTITY_ID)
from custom_components.homie.homie_classes import (HomieNode)

# TYPINGS
from homeassistant.helpers.typing import (HomeAssistantType, ConfigType)

# CONSTANTS
_LOGGER = logging.getLogger(__name__)
VALUE_PROP = 'value'

@asyncio.coroutine
def async_setup_platform(hass: HomeAssistantType, config: ConfigType, async_add_entities, discovery_info=None):
    """Set up the Homie sensor."""
    _LOGGER.info(f"Setting up Homie Sensor: {config} - {discovery_info}")

    entity_id = discovery_info[KEY_HOMIE_ENTITY_ID]
    homie_sensor_node = hass.data[KEY_HOMIE_ALREADY_DISCOVERED][entity_id]
    if homie_sensor_node is None: 
        raise ValueError("Homie Sensor faild to recive a Homie Node to bind too")
    if not homie_sensor_node._has_property(VALUE_PROP): 
        raise Exception(f"Homie Sensor Nodes doesnt have a {VALUE_PROP} property")
    
    async_add_entities([HomieSensor(entity_id, homie_sensor_node)])
    homie_sensor_node.is_setup = True
    return None


class HomieSensor(Entity):
    """Implementation of a Homie Sensor."""

    def __init__(self, entity_id: str, homie_sensor_node: HomieNode):
        """Initialize Homie Sensor."""
        self.entity_id_1 = entity_id
        self._node = homie_sensor_node

    @property
    def name(self):
        """Return the name of the Homie Sensor."""
        return self.entity_id_1

    @property
    def state(self):
        """Return the state of the Homie Sensor."""
        if self._node.has_property(VALUE_PROP):
            return self._node.property(VALUE_PROP).value
        return STATE_UNKNOWN

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'unit'

    @property
    def should_poll(self):
        return True
