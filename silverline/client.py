"""SilverLine system interface."""

import ssl

from threading import Semaphore
import paho.mqtt.client as mqtt

from .orchestrator import OrchestratorMixin


class Client(mqtt.Client, OrchestratorMixin):
    """SilverLine Interface.

    Parameters
    ----------
    mqtt : str
        MQTT host server address.
    mqtt_port : int
        MQTT host server port.
    http : str
        Orchestrator HTTP server address.
    http_port : int
        Orchestrator HTTP server port.
    pwd : str
        MQTT password file.
    mqtt_username : str
        MQTT username
    use_ssl : bool
        Use SSL (mqtt-secure) if True.
    connect : bool
        Connect to MQTT on initialization if True.
    handlers : BaseHandler[]
        List of message handlers to register callbacks for.
    """

    def __init__(
            self, mqtt="localhost", mqtt_port=1883, pwd="mqtt_pwd.txt",
            mqtt_username="cli", use_ssl=False, http="localhost",
            http_port=8000, connect=True, handlers=[]):

        self.callbacks = {}
        self.arts_api = "http://{}:{}/api".format(http, http_port)
        self.handlers = handlers

        super().__init__("LibSilverLine Client")

        if connect:
            self.semaphore = Semaphore()
            self.semaphore.acquire()

            with open(pwd, 'r') as f:
                passwd = f.read().rstrip('\n')
            self.username_pw_set(mqtt_username, passwd)
            if use_ssl:
                self.tls_set(cert_reqs=ssl.CERT_NONE)
            self.connect(mqtt, mqtt_port, 60)

            # Waiting for on_connect to release
            self.loop_start()
            self.semaphore.acquire()

    def on_connect(self, mqttc, obj, flags, rc):
        """On connect callback: register handlers, release main thread."""
        for h in self.handlers:
            def _handle(client, userdata, msg):
                return h.handle(h.decode(client, userdata, msg))
            self.subscribe(h.topic)
            self.message_callback_add(h.topic, _handle)

        if self.semaphore is not None:
            self.semaphore.release()

    def on_disconnect(self, client, userdata, rc):
        """Disconnection callback."""
        print("Disconnected: rc={} ({})".format(
            rc, mqtt.connack_string(rc)))

    def register_callback(self, topic, callback):
        """Subscribe to topic and register callback for that topic."""
        self.subscribe(topic)
        self.message_callback_add(topic, callback)

    def on_message(self, client, userdata, message):
        """Subscribed message handler."""
        print(
            "[Warning] message arrived topic without handler (should be "
            "impossible!): {}".format(message.topic))
