"""Base message handler class for reference."""

import json


class BaseHandler:
    """Base MQTT message handler.

    Includes a generic JSON message handler by default.

    Attributes
    ----------
    decode : callable (msg -> object)
        Decodes mqtt message (paho.mqtt.MQTTMessage) into arbitrary data type.
    handle : callable
        Handles data type returned by `decode`.
    topic : str
        Topic that this handler corresponds to.
    """

    def __init__(self):
        self.topic = None

    def decode(self, client, userdata, msg):
        """Decode generic JSON message."""
        payload = str(msg.payload.decode("utf-8", "ignore"))
        if (payload[0] == "'"):
            payload = payload[1:len(payload) - 1]
        return json.loads(payload)

    def handle(self, _):
        """Message handler.

        Overwrite this either in a class, or by assignment in the initializer.
        """
        raise NotImplementedError()
