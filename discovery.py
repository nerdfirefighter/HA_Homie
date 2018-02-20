# This file Replaces the file homeassistant/components/mqtt/discovery.py
import asyncio
import json
import logging
import re

import homeassistant.components.mqtt as mqtt
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.const import CONF_PLATFORM
from homeassistant.components.mqtt import CONF_STATE_TOPIC

_LOGGER = logging.getLogger(__name__)

messages = {}
nodes = {}

TOPIC_NODES = re.compile(r'(?P<prefix_topic>[$\w]+[-\w]*\w)/(?P<device>[$\w]+[-\w]*\w)/\$nodes')
TOPIC_ONLINE = re.compile(r'(?P<prefix_topic>[$\w]+[-\w]*\w)/(?P<device>[$\w]+[-\w]*\w)/\$online')

STATE_ONLINE = 'true'


@asyncio.coroutine
def async_start(hass, discovery_topic, hass_config):
    """Initialize of MQTT Discovery."""
    # pylint: disable=unused-variable
    @asyncio.coroutine
    def async_device_message_received(topic, payload, qos):
        """Process the received message."""
        #_LOGGER.warning("mqdiscover | [%s]:[%s]:[%s]", qos, topic, payload)
        
        # List of all topics published on MQTT since HA was started
        messages[topic] = payload
        
        # Check if the topic is a list of nodes
        match_nodes = TOPIC_NODES.match(topic)
        if match_nodes:
            arr = payload.split(",")
            nodelist = {}
            for a in arr:
                b = a.split(':')
                nodelist[b[0]] = b[1]
            device = match_nodes.group('device')
            nodes[device] = nodelist
            #for key, val in nodes.items():
                #for key2, val2 in val.items():
                    #_LOGGER.warning("Device:[%s] - Node:[%s] - Type:[%s]", key, key2, val2)
        
        # Check if topic is $online topic
        match_online = TOPIC_ONLINE.match(topic)
        if match_online:
            _LOGGER.warning("Online Match[%s]: %s", match_online.group('device'), payload)
            if payload.lower() == STATE_ONLINE:
                for key, val in nodes.items():
                    for key2, val2 in val.items():
                        _LOGGER.warning("Device:[%s] - Node:[%s] - Type:[%s]", key, key2, val2)
                        # Log all nodes and types when device is considered online

        return

    # Listen for all MQTT messages on base topic
    yield from mqtt.async_subscribe(
        hass, discovery_topic + '/#', async_device_message_received, 0)

    return True
