# IMPORTS
import logging
import re
from .mqtt_message import (MQTTMessage, DEFAULT_MQTT_MESSAGE)

# TYPES
from ._typing import (MessageQue)

# REGEX
DISCOVER_NODES = re.compile(r'(?P<prefix_topic>\w[-/\w]*\w)/(?P<device_id>\w[-\w]*\w)/\$properties')

# GLOBALS
_LOGGER = logging.getLogger(__name__)


# TODO: Fix this as we dont want to set to empty when no topic in dic
def _get_mqtt_message(topics: MessageQue, topic:str):
    return topics.get(topic, DEFAULT_MQTT_MESSAGE)


class HomieDevice:
    # A definition of a Homie Device

    def __init__(self, base_topic: str, device_id: str):
        _LOGGER.info(f"Homie Device Discovered. ID: {device_id}")
        self._nodes = list()
        self._base_topic = base_topic
        self._device_id = device_id
        self._prefix_topic = f'{base_topic}/{device_id}'

    def _update(self, topics: MessageQue):
        # Load Device Properties
        self._convention_version = _get_mqtt_message(topics, f'{self._prefix_topic}/$homie').payload
        self._online = _get_mqtt_message(topics, f'{self._prefix_topic}/$online').payload
        self._name = _get_mqtt_message(topics, f'{self._prefix_topic}/$name').payload
        self._ip = _get_mqtt_message(topics, f'{self._prefix_topic}/$localip').payload
        self._mac = _get_mqtt_message(topics, f'{self._prefix_topic}/$mac').payload

        # Load Device Stats Properties
        self._uptime = _get_mqtt_message(topics, f'{self._prefix_topic}/$stats/uptime').payload
        self._signal = _get_mqtt_message(topics, f'{self._prefix_topic}/$stats/signal').payload
        self._i = _get_mqtt_message(topics, f'{self._prefix_topic}/$stats/interval').payload

        # Load Firmware Properties
        self._fw_name = _get_mqtt_message(topics, f'{self._prefix_topic}/$fw/name').payload
        self._fw_version = _get_mqtt_message(topics, f'{self._prefix_topic}/$fw/version').payload
        self._fw_checksum = _get_mqtt_message(topics, f'{self._prefix_topic}/$fw/checksum').payload

        # Load Implementation Properties
        self._implementation = _get_mqtt_message(topics, f'{self._prefix_topic}/$implementation').payload

        # Load Nodes that are available for this Device
        self._discover_nodes(topics)
        for node in self._nodes:
            filtered_topics = {k:v for (k,v) in topics.items() if node._base_topic in k}
            node._update(filtered_topics)

    def _discover_nodes(self, topics: MessageQue):
        for topic, message in topics.items():
            node_match = DISCOVER_NODES.match(topic)
            if node_match:
                node_base_topic = node_match.group('prefix_topic')
                node_id = node_match.group('device_id')
                if not self._has_node(node_id):
                    node = HomieNode(self, node_base_topic, node_id)
                    self._nodes.append(node)

    def _has_node(self, node_id: str):
        if self._get_node(node_id) is None:
            return False
        return True

    def _get_node(self, node_id: str):
        for node in self._nodes:
            if node.node_id == node_id:
                return node
        return None

    @property
    def base_topic(self):
        """Return the Base Topic of the device."""
        return self._base_topic

    @property
    def device_id(self):
        """Return the Device ID of the device."""
        return self._device_id

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def home_version(self):
        """Return the Homie Framework Version of the device."""
        return self._convention_version

    @property
    def online(self):
        """Return true if the device is online."""
        return self._online

    @property
    def ip(self):
        """Return the IP of the device."""
        return self._ip

    @property
    def mac(self):
        """Return the MAC of the device."""
        return self._mac

    @property
    def uptime(self):
        """Return the Uptime of the device."""
        return self._uptime

    @property
    def uptime(self):
        """Return the Signal of the device."""
        return self._signal

    @property
    def stats_interval(self):
        """Return the Stats Interval of the device."""
        return self._stats_interval

    @property
    def firmware_name(self):
        """Return the Firmware Name of the device."""
        return self._fw_name

    @property
    def firmware_version(self):
        """Return the Firmware Version of the device."""
        return self._fw_version

    @property
    def firmware_checksum(self):
        """Return the Firmware Checksum of the device."""
        return self._fw_checksum

    @property
    def nodes(self):
        """Return a List of Nodes for the device."""
        return self._nodes

    def node(self, node_id):
        """Return a specific Node for the device."""
        return self._get_node(node_name)
    
    def __str__(self):
        return f"{self.device_id} - {self.name} - {len(self.nodes)}"


class HomieNode:
    # A definition of a Homie Node
    def __init__(self, device: HomieDevice, base_topic: str, node_id: str):
        _LOGGER.info(f"Homie Node Discovered. ID: {node_id}")
        self._device = device
        self._properties = list()
        self._base_topic = base_topic
        self._node_id = node_id
        self._prefix_topic = f'{base_topic}/{node_id}'
        self._is_setup = False

    def _update(self, topics: MessageQue):
        # Load Node Properties
        self._type = _get_mqtt_message(topics, f'{self._prefix_topic}/$type').payload

        # load Properties that are avaliable to this Node
        self._discover_property(topics)
        for property in self._properties:
            filtered_topics = {k:v for (k,v) in topics.items() if property._base_topic in k}
            property._update(filtered_topics)

    def _discover_property(self, topics: MessageQue):
        properties_message = _get_mqtt_message(topics, f'{self._prefix_topic}/$properties').payload
        if properties_message:
            properties = properties_message.split(',')
            for property_id in properties:
                if not self._has_property(property_id):
                    property = HomieProperty(self, self._prefix_topic, property_id, False)
                    self._properties.append(property)

    def _has_property(self, property_id: str):
        if self._get_property(property_id) is None:
            return False
        return True

    def _get_property(self, property_id: str):
        for property in self._properties:
            if property.property_id == property_id:
                return property
        return None

    @property
    def base_topic(self):
        """Return the Base Topic of the node."""
        return self._base_topic

    @property
    def node_id(self):
        """Return the Node Id of the node."""
        return self._node_id

    @property
    def type(self):
        """Return the Type of the node."""
        return self._type
    
    @property
    def is_setup(self):
        """Return True if the node has been setup as a component"""
        return self._is_setup
    @is_setup.setter
    def is_setup(self, value: bool):
        self._is_setup = value

    @property
    def properties(self):
        """Return a List of properties for the node."""
        return self._properties

    def has_property(self, property_name: str):
        """Return a specific Property for the node."""
        return self._has_property(property_name)

    def property(self, property_name: str):
        """Return a specific Property for the node."""
        return self._get_property(property_name)


class HomieProperty:
    # A definition of a Homie Property
    def __init__(self, node: HomieNode, base_topic: str, property_id: str, settable: bool):
        _LOGGER.info(f"Homie Property Discovered. ID: {property_id}")
        self._node = node
        self._base_topic = base_topic
        self._property_id = property_id
        self._settable = settable
        self._prefix_topic = f'{base_topic}/{property_id}'

        self._value = None

    def _update(self, topics: MessageQue):
        self._value = _get_mqtt_message(topics, self._prefix_topic).payload

    @property
    def property_id(self):
        """Return the Property Id of the Property."""
        return self._property_id
    
    @property
    def value(self):
        """Return the value of the Property."""
        return self._value

    @property
    def settable(self):
        """Return the Settablity of the Property."""
        return self._settable

    @property
    def name(self):
        """Return the Name of the Property."""
        return self._name

    @property
    def unit(self):
        """Return the Unit for the Property."""
        return self._unit

    @property
    def dataType(self):
        """Return the Data Type for the Property."""
        return self._datatype

    @property
    def format(self):
        """Return the Format for the Property."""
        return self._format
