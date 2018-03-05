# IMPORTS
import asyncio
import logging
import re
import time
import voluptuous as vol


import homeassistant.components.mqtt as mqtt
from homeassistant.components.mqtt import (CONF_DISCOVERY_PREFIX, CONF_QOS, valid_discovery_topic, _VALID_QOS_SCHEMA)
from homeassistant.helpers.discovery import (async_load_platform)
from homeassistant.helpers import (config_validation as cv)
from homeassistant.const import (EVENT_HOMEASSISTANT_STOP)
from .mqtt_message import (MQTTMessage)
from .homie_classes import (HomieDevice)

# TYPES
from typing import (Dict, List, Callable)
from homeassistant.helpers.typing import (HomeAssistantType, ConfigType)
from ._typing import (MessageQue)

Devices = List[HomieDevice]

# REGEX
DISCOVER_DEVICE = re.compile(r'(?P<prefix_topic>\w[-/\w]*\w)/(?P<device_id>\w[-\w]*\w)/\$homie')


# CONSTANTS
DOMAIN = 'homie'
DEPENDENCIES = ['mqtt']
INTERVAL_SECONDS = 1
MESSAGE_MAX_KEEP_SECONDS = 5
HOMIE_SUPPORTED_VERSION = '2.0.0'
DEFAULT_DISCOVERY_PREFIX = 'homie'
DEFAULT_QOS = 1

# CONFIg
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_DISCOVERY_PREFIX, default=DEFAULT_DISCOVERY_PREFIX): valid_discovery_topic,
        vol.Optional(CONF_QOS, default=DEFAULT_QOS): _VALID_QOS_SCHEMA,
    }),
}, extra=vol.ALLOW_EXTRA)

# GLOBALS
_LOGGER = logging.getLogger(__name__)
_Task: asyncio.Task
_MQTT_MESSAGES: Dict[str, MQTTMessage] = dict()
_DEVICES: Devices = list()


async def async_setup(hass: HomeAssistantType, config: ConfigType):
    """Setup the Homie service."""
    _LOGGER.info(f"Component - {DOMAIN} - Setup")

    # Config
    conf = config.get(DOMAIN)
    if conf is None:
        conf = CONFIG_SCHEMA({DOMAIN: {}})[DOMAIN]
    
    discovery_prefix = conf.get(CONF_DISCOVERY_PREFIX)
    qos = conf.get(CONF_QOS)

    # Create Proccess Task
    _Task = hass.loop.create_task(async_interval())
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_destroy)

    # Sart
    await async_start(hass, discovery_prefix, qos)

    return True


async def async_destroy(event):
    _LOGGER.info(f"Component - {DOMAIN} - Destroy")
    if _Task:
        _Task.cancel()


async def async_start(hass: HomeAssistantType, discovery_prefix: str, qos:int):
    """Start the Homie service."""
    _LOGGER.info(f"Component - {DOMAIN} - Start. Discovery Topic: {discovery_prefix}/")
    await mqtt.async_subscribe(hass, f'{discovery_prefix}/#', async_device_message_received, qos)
    return True


async def async_device_message_received(topic: str, payload: str, qos: int):
    message = MQTTMessage(topic, payload, qos)
    _MQTT_MESSAGES[topic] = message
    async_proccess_messages()


async def async_interval():
    while True:
        async_proccess_messages()
        remove_messages()
        await asyncio.sleep(INTERVAL_SECONDS)


def async_proccess_messages():
    discover_devices()
    for device in _DEVICES:
        device._update(_MQTT_MESSAGES)
    remove_messages()
   

def remove_messages():
    to_remove = list()
    # Remove old message from the que
    for topic, message in _MQTT_MESSAGES.items():
        if message.seen or (time.clock() - message.timeStamp) > MESSAGE_MAX_KEEP_SECONDS:
            to_remove.append(topic)
    for topic in to_remove:
        del _MQTT_MESSAGES[topic]


def has_device(device_id: str):
    for device in _DEVICES:
        if device.device_id == device_id:
            return True
    return False


def discover_devices():
    for topic, message in _MQTT_MESSAGES.items():
        device_match = DISCOVER_DEVICE.match(topic)
        if device_match and message.payload == HOMIE_SUPPORTED_VERSION:
            device_base_topic = device_match.group('prefix_topic')
            device_id = device_match.group('device_id')
            if not has_device(device_id):
                device = HomieDevice(device_base_topic, device_id, _MQTT_MESSAGES)
                _DEVICES.append(device)


def setup_device_components():
    for device in _DEVICES:
        # Do device relate component Suff

        # Do Node related component stuff

