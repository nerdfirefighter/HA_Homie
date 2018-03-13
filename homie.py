# IMPORTS
import asyncio
import logging
import re
import time
import datetime
import voluptuous as vol

import homeassistant.components.mqtt as mqtt
from homeassistant.components.mqtt import (CONF_DISCOVERY_PREFIX, CONF_QOS, valid_discovery_topic, _VALID_QOS_SCHEMA)
from homeassistant.helpers.discovery import (async_load_platform)
from homeassistant.helpers.event import (async_track_time_interval)
from homeassistant.helpers import (config_validation as cv)
from homeassistant.const import (EVENT_HOMEASSISTANT_STOP)
from .mqtt_message import (MQTTMessage)
from .homie_classes import (HomieDevice, HomieNode, HomieProperty)

# TYPES
from typing import (Dict, List, Callable)
from homeassistant.helpers.typing import (HomeAssistantType, ConfigType)
from ._typing import (MessageQue)
Devices = Dict[str, HomieDevice]
MessageQue = Dict[str, MQTTMessage]

# REGEX
DISCOVER_DEVICE = re.compile(r'(?P<prefix_topic>\w[-/\w]*\w)/(?P<device_id>\w[-\w]*\w)/\$homie')
DISCOVER_NODES = re.compile(r'(?P<prefix_topic>\w[-/\w]*\w)/(?P<device_id>\w[-\w]*\w)/\$properties')

# CONSTANTS
DOMAIN = 'homie'
DEPENDENCIES = ['mqtt']
INTERVAL_SECONDS = 1
MESSAGE_MAX_KEEP_SECONDS = 5
HOMIE_SUPPORTED_VERSION = '2.0.0'
DEFAULT_DISCOVERY_PREFIX = 'homie'
DEFAULT_QOS = 0
KEY_HOMIE_ALREADY_DISCOVERED = 'KEY_HOMIE_ALREADY_DISCOVERED'
KEY_HOMIE_ENTITY_ID = 'KEY_HOMIE_ENTITY_ID'

# CONFIg
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_DISCOVERY_PREFIX, default=DEFAULT_DISCOVERY_PREFIX): valid_discovery_topic,
        vol.Optional(CONF_QOS, default=DEFAULT_QOS): _VALID_QOS_SCHEMA,
    }),
}, extra=vol.ALLOW_EXTRA)

# GLOBALS
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistantType, config: ConfigType):
    """Setup the Homie service."""
    # Init
    _DEVICES = dict()
    hass.data[KEY_HOMIE_ALREADY_DISCOVERED] = dict()

    # Config
    conf = config.get(DOMAIN)
    if conf is None:
        conf = CONFIG_SCHEMA({DOMAIN: {}})[DOMAIN]
    discovery_prefix = conf.get(CONF_DISCOVERY_PREFIX)
    qos = conf.get(CONF_QOS)

    # Destroy Homie
    async def async_destroy(event):
        # TODO: unsub?
        pass
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_destroy)

    # Sart
    async def async_start():
        _LOGGER.info(f"Component - {DOMAIN} - Start. Discovery Topic: {discovery_prefix}/")
        await from mqtt.async_subscribe(hass, f'{discovery_prefix}/+/$homie', async_discover_message_received, qos)

    async def async_discover_message_received(topic: str, payload: str, qos: int):
        device_match = DISCOVER_DEVICE.match(topic)
            if device_match and payload == HOMIE_SUPPORTED_VERSION:
                device_base_topic = device_match.group('prefix_topic')
                device_id = device_match.group('device_id')
                if device_id not in _DEVICES:
                    _DEVICES[device_id] = HomieDevice(hass, device_base_topic, device_id, {"qos":qos})
    
    async def async_setup_device_components():
        for device in _DEVICES:
            #_LOGGER.info(f"Device {device.device_id}")
            # Do device relate component Suff
            # TODO: create device sneosors for stats

            # Do Node related component stuff
            for node in device.nodes:
                if not node.is_setup:
                    def get_entity_id():
                        return f"{device.device_id}_{node.node_id}"

                    if node.type == 'sensor':
                        await from setup_device_node_as_platform(get_entity_id(), node, 'sensor')
                    elif node.type == 'switch':
                        None

    async def setup_device_node_as_platform(entity_id: str, node: HomieNode, platform: str):
        hass.data[KEY_HOMIE_ALREADY_DISCOVERED][entity_id] = node
        discovery_info = {KEY_HOMIE_ENTITY_ID: entity_id}
        await from async_load_platform(hass, platform, DOMAIN, discovery_info)


    await from async_start()
    return True


# Types
class MQTTMessage:
    def __init__(self, topic: str, payload: str, qos: int):
        self._topic = topic
        self._payload = payload
        self._qos = qos
        self._seen = False
        self._time_stamp = time.clock()

    @property
    def topic(self):
        """Return the topic of the message."""
        return self._topic

    @property
    def payload(self):
        """Return the payload of the message."""
        self._seen = True
        return self._payload

    @property
    def qos(self):
        """Return the qos of the message."""
        return self._qos

    @property
    def seen(self):
        """Return true if the message has been seen"""
        return self._seen

    @property
    def time_stamp(self):
        """Return the time stamp of the message."""
        return self._time_stamp


DEFAULT_MQTT_MESSAGE = MQTTMessage('', '', 0)


# TODO: Fix this as we dont want to set to empty when no topic in dic
def _get_mqtt_message(topics: MessageQue, topic:str):
    return topics.get(topic, DEFAULT_MQTT_MESSAGE)


class HomieDevice:
    # A definition of a Homie Device
    def __init__(self, hass:HomeAssistantType, base_topic: str, device_id: str, options: dict):
        _LOGGER.info(f"Homie Device Discovered. ID: {device_id}")
        self._nodes = dict()
        self._base_topic = base_topic
        self._device_id = device_id
        self._prefix_topic = f'{base_topic}/{device_id}'

        async def async_discover_message_received(topic: str, payload: str, qos: int):
            node_match = DISCOVER_NODES.match(topic)
            if node_match:
                node_base_topic = node_match.group('prefix_topic')
                node_id = node_match.group('device_id')
                if node_id not in self._nodes:
                    self._nodes[node_id] = HomieNode(hass, self, node_base_topic, node_id, {**options})

        await mqtt.async_subscribe(hass, f'{this._prefix_topic}/+/$properties', async_discover_message_received, options['qos'])
        await mqtt.async_subscribe(hass, f'{this._prefix_topic}', self._update, options['qos'])

    async def _update(self, topic: str, payload: str, qos: int):
        # Load Device Properties
        if f'{self._prefix_topic}/$homie' in topic: self._convention_version = payload
        self._convention_version = _get_mqtt_message(topics, f'{self._prefix_topic}/$homie').payload
        self._online = _get_mqtt_message(topics, f'{self._prefix_topic}/$online').payload
        self._name = _get_mqtt_message(topics, f'{self._prefix_topic}/$name').payload
        self._ip = _get_mqtt_message(topics, f'{self._prefix_topic}/$localip').payload
        self._mac = _get_mqtt_message(topics, f'{self._prefix_topic}/$mac').payload

        # Load Device Stats Properties
        self._uptime = _get_mqtt_message(topics, f'{self._prefix_topic}/$stats/uptime').payload
        self._signal = _get_mqtt_message(topics, f'{self._prefix_topic}/$stats/signal').payload
        self._stats_interval = _get_mqtt_message(topics, f'{self._prefix_topic}/$stats/interval').payload

        # Load Firmware Properties
        self._fw_name = _get_mqtt_message(topics, f'{self._prefix_topic}/$fw/name').payload
        self._fw_version = _get_mqtt_message(topics, f'{self._prefix_topic}/$fw/version').payload
        self._fw_checksum = _get_mqtt_message(topics, f'{self._prefix_topic}/$fw/checksum').payload

        # Load Implementation Properties
        self._implementation = _get_mqtt_message(topics, f'{self._prefix_topic}/$implementation').payload

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
    def homie_version(self):
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
    def signal(self):
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
        return self._nodes[node_name]
    
    def __str__(self):
        return f"{self.device_id} - {self.name} - {len(self.nodes)}"


class HomieNode:
    # A definition of a Homie Node
    def __init__(self, hass: HomeAssistantType, device: HomieDevice, base_topic: str, node_id: str, options: dict):
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
