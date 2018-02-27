# IMPORTS
import asyncio
import json
import logging
import re

import homeassistant.components.mqtt as mqtt
from homeassistant.helpers.discovery import async_load_platform
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
#from homie_classes import HomieDevice, HomieNode, HomieProperty

# TYPES
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers import ConfigType

# CONSTANTS
DOMAIN = 'homie'
DEPENDENCIES = ['mqtt']
CONFG_DISCOVERY_PREFIX = "discovery_prefix"

# GLOBALS
_LOGGER = logging.getLogger(__name__)


@asyncio.coroutine
def async_setup(hass: HomeAssistantType, config: ConfigType):
    # Entry Point
    _LOGGER.info(f"{DOMAIN} - Started")

    return True


@asyncio.coroutine
def async_start(hass, discovery_topic, hass_config):
    yield from mqtt.async_subscribe(hass, discovery_topic + '/#', async_device_message_received, 0)


@asyncio.coroutine
def async_device_message_received(topic, payload, qos):
