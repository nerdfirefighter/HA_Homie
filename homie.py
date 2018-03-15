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
from homeassistant.const import (EVENT_HOMEASSISTANT_STOP, STATE_UNKNOWN)
from homeassistant.core import (callback)
# TYPES
from typing import (Dict, List)
from homeassistant.helpers.typing import (HomeAssistantType, ConfigType)

# REGEX
DISCOVER_DEVICE = re.compile(r'(?P<prefix_topic>\w[-/\w]*\w)/(?P<device_id>\w[-\w]*\w)/\$homie')
DISCOVER_NODES = re.compile(r'(?P<prefix_topic>\w[-/\w]*\w)/(?P<node_id>\w[-\w]*\w)/\$properties')
DISCOVER_PROPERTIES = re.compile(r'(?P<property_id>\w[-/\w]*\w)(\[(?P<range_start>[0-9])-(?P<range_end>[0-9]+)\])?(?P<settable>:settable)?')

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
    # async def async_destroy(event):
    #     # TODO: unsub?
    #     pass
    # hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_destroy)

    # Sart
    async def async_start():
        _LOGGER.info(f"Component - {DOMAIN} - Start. Discovery Topic: {discovery_prefix}/")
        await mqtt.async_subscribe(hass, f'{discovery_prefix}/+/$homie', async_discover_message_received, qos)

    async def async_discover_message_received(topic: str, payload: str, qos: int):
        device_match = DISCOVER_DEVICE.match(topic)
        if device_match and payload == HOMIE_SUPPORTED_VERSION:
            device_base_topic = device_match.group('prefix_topic')
            device_id = device_match.group('device_id')
            if device_id not in _DEVICES:
                device = HomieDevice(device_base_topic, device_id)
                await device._async_setup(hass, qos)
                _DEVICES[device_id] = device
    
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
                        await setup_device_node_as_platform(get_entity_id(), node, 'sensor')
                    elif node.type == 'switch':
                        None

    async def setup_device_node_as_platform(entity_id: str, node: HomieNode, platform: str):
        hass.data[KEY_HOMIE_ALREADY_DISCOVERED][entity_id] = node
        discovery_info = {KEY_HOMIE_ENTITY_ID: entity_id}
        await async_load_platform(hass, platform, DOMAIN, discovery_info)


    await async_start()
    return True


# Types
class ChangeListener(object):
    def __init__(self):
        super(ChangeListener, self).__init__()
        self._listeners = list()

    def __setattr__(self, name: str, value: str):
        super(ChangeListener, self).__setattr__(name, value)
        for action in self._listeners: action()

    @callback
    def add_listener(self, action):
        self._listeners.append(action)

class HomieDevice(ChangeListener):
    # A definition of a Homie Device
    def __init__(self, base_topic: str, device_id: str):
        super(HomieDevice, self).__init__()
        _LOGGER.info(f"Homie Device Discovered. ID: {device_id}")
        self._nodes = dict()
        self._base_topic = base_topic
        self._device_id = device_id
        self._prefix_topic = f'{base_topic}/{device_id}'

        self._convention_version = STATE_UNKNOWN
        self._online = STATE_UNKNOWN
        self._name = STATE_UNKNOWN
        self._ip = STATE_UNKNOWN
        self._mac = STATE_UNKNOWN
        self._uptime = STATE_UNKNOWN
        self._signal = STATE_UNKNOWN
        self._stats_interval = STATE_UNKNOWN
        self._fw_name = STATE_UNKNOWN
        self._fw_version = STATE_UNKNOWN
        self._fw_checksum = STATE_UNKNOWN
        self._implementation = STATE_UNKNOWN
        
    async def _async_setup(self, hass:HomeAssistantType, qos):
        async def async_discover_message_received(topic: str, payload: str, qos: int):
            node_match = DISCOVER_NODES.match(topic)
            if node_match:
                node_base_topic = node_match.group('prefix_topic')
                node_id = node_match.group('node_id')
                if node_id not in self._nodes:
                    node = HomieNode(self, node_base_topic, node_id)
                    await node._async_setup(hass, qos, payload)
                    self._nodes[node_id] = node

        await mqtt.async_subscribe(hass, f'{self._prefix_topic}/+/$properties', async_discover_message_received, qos)
        await mqtt.async_subscribe(hass, f'{self._prefix_topic}', self._async_update, qos)

    async def _async_update(self, topic: str, payload: str, qos: int):
        topic = topic.replace(f'{self._prefix_topic}/', '')
        # Load Device Properties
        if topic == '$homie': self._convention_version = payload
        if topic == '$homie': self._convention_version = payload
        if topic == '$online': self._online = payload
        if topic == '$name': self._name = payload
        if topic == '$localip': self._ip = payload
        if topic == '$mac': self._mac = payload

        # Load Device Stats Properties
        if topic == '$stats/uptime': self._uptime = payload
        if topic == '$stats/signal': self._signal = payload
        if topic == '$stats/interval': self._stats_interval = payload

        # Load Firmware Properties
        if topic == '$fw/name': self._fw_name = payload
        if topic == '$fw/version': self._fw_version = payload
        if topic == '$fw/checksum': self._fw_checksum = payload

        # Load Implementation Properties
        if topic == '$implementation': self._implementation = payload

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
        """Return a Dict of Nodes for the device."""
        return self._nodes

    def node(self, node_id):
        """Return a specific Node for the device."""
        return self._nodes[node_name]


class HomieNode(ChangeListener):
    # A definition of a Homie Node
    def __init__(self, device: HomieDevice, base_topic: str, node_id: str):
        super(HomieNode, self).__init__()
        _LOGGER.info(f"Homie Node Discovered. ID: {node_id}")
        self._device = device
        self._properties = dict()
        self._base_topic = base_topic
        self._node_id = node_id
        self._prefix_topic = f'{base_topic}/{node_id}'
        self._is_setup = False

        self._type = STATE_UNKNOWN

    async def _async_setup(self, hass: HomeAssistantType, qos: int, properties_str: str):
        for property_match in DISCOVER_PROPERTIES.finditer(properties_str):
            property_id = property_match.group('property_id')
            if property_id not in self._properties:
                property_settable = True if property_match.group('settable') is not None else False
                property_range = (int(property_match.group('range_start')), int(property_match.group('range_end'))) if property_match.group('range_start') is not None else ()
                property = HomieProperty(self, self._prefix_topic, property_id, property_settable, property_range)
                await property._async_setup(hass, qos)
                self._properties[property_id] = property

        await mqtt.async_subscribe(hass, f'{self._prefix_topic}', self._async_update, qos)


    async def _async_update(self, topic: str, payload: str, qos: int):
        topic = topic.replace(f'{self._prefix_topic}/', '')
        # Load Node Properties
        if topic == '$type': self._type = payload

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
        """Return a Dict of properties for the node."""
        return self._properties

    def has_property(self, property_name: str):
        """Return a specific Property for the node."""
        return property_name in self._properties

    def property(self, property_name: str):
        """Return a specific Property for the node."""
        return self._properties[property_name]


class HomieProperty(ChangeListener):
    # A definition of a Homie Property
    def __init__(self, node: HomieNode, base_topic: str, property_id: str, settable: bool, range_tup: tuple):
        super(HomieProperty, self).__init__()
        _LOGGER.info(f"Homie Property Discovered. ID: {property_id}")
        self._node = node
        self._base_topic = base_topic
        self._property_id = property_id
        self._settable = settable
        self._range = range_tup
        self._prefix_topic = f'{base_topic}/{property_id}'

        self._value = STATE_UNKNOWN
    
    async def _async_setup(self, hass: HomeAssistantType, qos: int):
        await mqtt.async_subscribe(hass, f'{self._prefix_topic}', self._async_update, qos)

    async def _async_update(self, topic: str, payload: str, qos: int):
        if topic == self._prefix_topic: self._value = payload

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
