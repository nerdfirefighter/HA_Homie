# IMPORT
import time


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
    def timeStamp(self):
        """Return the time stamp of the message."""
        return self._time_stamp


DEFAULT_MQTT_MESSAGE = MQTTMessage('', '', 0)
