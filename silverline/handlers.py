"""Base message handler class for reference."""


class BaseHandler:
    """Base MQTT message handler.

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
        self.handle = None
        self.decode = None
