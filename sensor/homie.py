# IMPORT
import asyncio
import logging

from homeassistant.helpers.entity import (Entity)
from custom_components.homie import (KEY_HOMIE_DEVICES, KEY_HOMIE_DEVICE_ID, KEY_HOMIE_NODE_ID)
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
    homie_sensor_node = get_node(hass, discovery_info[KEY_HOMIE_DEVICE_ID], discovery_info[KEY_HOMIE_NODE_ID])
    if homie_sensor_node is None: raise ValueError("Homie Sensor faild to recive a Homie Node to bind too")
    if not homie_sensor_node._has_property(VALUE_PROP): raise Exception(f"Homie Sensor Nodes doesnt have a {VALUE_PROP} property")
    
    _LOGGER.info("Added Homie Sensor")
    async_add_entities([HomieSensor(homie_sensor_node)], True)


def get_node(hass: HomeAssistantType, device_id: str, node_id: str):
    for device in hass.data[KEY_HOMIE_DEVICES]:
        if device.device_id == device_id:
            for node in device.nodes:
                if node.node_id == node_id:
                    return node
    return None


class HomieSensor(Entity):
    """Implementation of a Homie Sensor."""

    def __init__(self, homie_sensor_node: HomieNode):
        """Initialize Homie Sensor."""
        self._node = homie_sensor_node

    @property
    def name(self):
        """Return the name of the Homie Sensor."""
        return self._node.node_id

    @property
    def state(self):
        """Return the state of the Homie Sensor."""
        return 10  # self._node.property(VALUE_PROP)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'unit'

    @property
    def should_poll(self):
        return False

    def update(self):
        None