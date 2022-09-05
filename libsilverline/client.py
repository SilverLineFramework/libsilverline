"""SilverLine system interface."""

import ssl
import uuid
import logging

from threading import Semaphore
import paho.mqtt.client as mqtt

from .orchestrator import OrchestratorMixin
from .profile import ProfileMixin


class Client(mqtt.Client, OrchestratorMixin, ProfileMixin):
    """SilverLine Interface Python Client.

    This class provides access to Silverline Services REST and Pubsub APIs;
    SilverLine services also use this class as a primary interface into
    SilverLine.

    Parameters
    ----------
    cid : str
        MQTT client ID. A random UUID is appended to ensure that CID collisions
        cannot occur.
    mqtt : str
        MQTT host server address.
    mqtt_port : int
        MQTT host server port.
    realm : str
        Realm name.
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
    """

    def __init__(
            self, cid="libsilverline", mqtt="localhost", mqtt_port=1883,
            realm="realm", pwd="mqtt_pwd.txt", mqtt_username="cli",
            use_ssl=False, http="localhost", http_port=8000, connect=True):

        self.callbacks = {}
        self.arts_api = "http://{}:{}/api".format(http, http_port)
        self.realm = realm
        self.mqtt_control = "/".join([realm, "proc", "control"])

        self.log = logging.getLogger('client')

        # Append a UUID here since client_id must be unique.
        # If this is not added, MQTT will disconnect with rc=7
        # (Connection Refused: unknown reason.)
        cid = "{}:{}".format(cid, uuid.uuid4())
        super().__init__(client_id=cid)

        if connect:
            self.semaphore = Semaphore()
            self.semaphore.acquire()

            self.log.info("Connecting with MQTT client: {}".format(cid))
            self.log.info("SSL: {}".format(use_ssl))
            self.log.info("Username: {}".format(mqtt_username))
            try:
                with open(pwd, 'r') as f:
                    passwd = f.read().rstrip('\n')
                self.log.info("Password file: {}".format(pwd))
            except FileNotFoundError:
                passwd = ""
                self.log.warn("No password supplied; using an empty password.")

            self.username_pw_set(mqtt_username, passwd)
            if use_ssl:
                self.tls_set(cert_reqs=ssl.CERT_NONE)
            self.connect(mqtt, mqtt_port, 60)

            # Waiting for on_connect to release
            self.loop_start()
            self.semaphore.acquire()

    def on_connect(self, mqttc, obj, flags, rc):
        """On connect callback: register handlers, release main thread."""
        if self.semaphore is not None:
            self.semaphore.release()
        self.log.info("Connected to MQTT server.")

    def on_disconnect(self, client, userdata, rc):
        """Disconnection callback."""
        self.log.warn("Disconnected: rc={} ({})".format(
            rc, mqtt.connack_string(rc)))

    def register_callback(self, topic, callback):
        """Subscribe to topic and register callback for that topic."""
        self.subscribe(topic)
        self.message_callback_add(topic, callback)

    def register_handler(self, handler):
        """Subscribe and register callback for handler."""
        def _handle(client, userdata, msg, handler=handler):
            try:
                return handler.handle(handler.decode(client, userdata, msg))
            except Exception as e:
                self.log.error(
                    "{} @ {}: {}".format(str(e), msg.topic, msg.payload[:64]))
                raise(e)
        self.register_callback(handler.topic, _handle)

    def on_message(self, client, userdata, message):
        """Subscribed message handler."""
        self.log.warn(
            "Message arrived topic without handler (should be "
            "impossible!): {}".format(message.topic))
