# IMPORTS
import asyncio
import logging
import re
import time

import homeassistant.components.mqtt as mqtt
from homeassistant.helpers.discovery import (async_load_platform)
from homeassistant.const import (
    CONF_FORCE_UPDATE, CONF_NAME,
    CONF_VALUE_TEMPLATE, STATE_UNKNOWN,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_PLATFORM
)
from homeassistant.components.mqtt import (
    CONF_AVAILABILITY_TOPIC,
    CONF_STATE_TOPIC,
    CONF_PAYLOAD_AVAILABLE,
    CONF_PAYLOAD_NOT_AVAILABLE,
    CONF_QOS
)
from homeassistant.const import (EVENT_HOMEASSISTANT_STOP)
from .mqtt_message import (MQTTMessage)
from .homie_classes import (HomieDevice)

# TYPES
from typing import (Dict, List, Callable)
from homeassistant.helpers.typing import (HomeAssistantType, ConfigType)
from ._typing import (MessageQue)

Devices = List[HomieDevice]

# RegEx
DISCOVER_DEVICE = re.compile(r'(?P<prefix_topic>\w[-/\w]*\w)/(?P<device_id>\w[-\w]*\w)/\$homie')


# CONSTANTS
DOMAIN = 'homie'
DEPENDENCIES = ['mqtt']
INTERVAL_SECONDS = 1
MESSAGE_MAX_KEEP_SECONDS = 5
CONFG_DISCOVERY_PREFIX = 'discovery_prefix'
HOMIE_SUPPORTED_VERSION = '2.0.0'

# GLOBALS
_LOGGER = logging.getLogger(__name__)
_Task: asyncio.Task = None
_DISCOVERY_PREFIX = 'homie/'
_MQTT_MESSAGES: Dict[str, MQTTMessage] = dict()
_DEVICES: Devices = list()


async def async_setup(hass: HomeAssistantType, config: ConfigType):
    # Entry Point
    _LOGGER.info(f"Component - {DOMAIN} - Setup")

    # Create Proccess Task
    _Task = hass.loop.create_task(async_interval())
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_destroy)

    # Sart
    await async_start(hass, config)

    return True


async def async_destroy(event):
    _LOGGER.info(f"Component - {DOMAIN} - Destroy")
    _Task.cancel()


async def async_start(hass: HomeAssistantType, config: ConfigType):
    _LOGGER.info(f"Component - {DOMAIN} - Start")
    await mqtt.async_subscribe(hass, f'{_DISCOVERY_PREFIX}/#', async_device_message_received, 1)


async def async_device_message_received(topic: str, payload: str, qos: int):
    message = MQTTMessage(topic, payload, qos)
    _MQTT_MESSAGES[topic] = message
    async_proccess_messages()


async def async_interval():
    while True:
        # Process messages
        async_proccess_messages()
        # Remove old message from the que
        for topic, message in _MQTT_MESSAGES.items():
            if (time.clock() - message.timeStamp) > MESSAGE_MAX_KEEP_SECONDS:
                del _MQTT_MESSAGES[topic]
        await asyncio.sleep(INTERVAL_SECONDS)


async def async_proccess_messages():
    discover_devices(_MQTT_MESSAGES)
    for device in _DEVICES:
        device._update(_MQTT_MESSAGES)
    # Remove seen messages from queu
    for topic, message in _MQTT_MESSAGES.items():
        if message.seen:
            del _MQTT_MESSAGES[topic]


def discover_devices():
    for topic, message in _MQTT_MESSAGES.items():
        device_match = DISCOVER_DEVICE.match(topic)
        if device_match and message.payload == HOMIE_SUPPORTED_VERSION:
            device_base_topic = device_match.group('prefix_topic')
            device_id = device_match.group('device_id')
            if not has_device(device_id):
                device = HomieDevice(
                    device_base_topic, device_id, _MQTT_MESSAGES)
                _DEVICES.append(device)


def has_device(device_id: str):
    for device in _DEVICES:
        if device.device_id == device_id:
            return True
    return False
