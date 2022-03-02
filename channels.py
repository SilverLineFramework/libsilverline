"""Channels interface."""

import ssl
import queue

from threading import Semaphore
import paho.mqtt.client as mqtt


class Channel:
    """Opened channel.

    Parameters
    ----------
    topic : str
        Topic to subscribe to.
    """

    def __init__(self, topic, parent):
        self.topic = topic
        self.parent = parent
        self.messages = queue.Queue()

    def read(self):
        """Read message from queue."""
        return self.messages.get()

    def write(self, msg):
        """Write message to MQTT."""
        self.parent.publish(self.topic, msg)

    def close(self):
        """Close this channel."""
        self.parent.unsubscribe(self.topic)

    def poll(self, sleep_ms):
        """Wait for message on queue."""
        try:
            return self.messages.get(timeout=sleep_ms / 1000)
        except queue.Empty:
            return None


class Channels(mqtt.Client):
    """Channels interface.

    Keyword Args
    ------------
    host : str
        MQTT host server address.
    port : int
        MQTT host server port.
    pwd : str
        MQTT password file
    username : str
        MQTT username
    ssl : bool
        Whether to use SSL.
    """

    def __init__(
            self, host="localhost", port=1883, pwd="mqtt_pwd.txt",
            username="cli", use_ssl=False):

        super().__init__("Python Special Runtime")

        self.init_semaphore = Semaphore()
        self.init_semaphore.acquire()

        with open(pwd, 'r') as f:
            passwd = f.read().rstrip('\n')
        self.username_pw_set(username, passwd)
        if use_ssl:
            self.tls_set(cert_reqs=ssl.CERT_NONE)
        self.connect(host, port, 60)

        self.loop_start()
        self.init_semaphore.acquire()

        self.channels = {}

    def on_connect(self, mqttc, obj, flags, rc):
        """On connect callback."""
        print("[Setup] Connected: rc={} ({})".format(
            rc, mqtt.connack_string(rc)))
        self.init_semaphore.release()

    def on_disconnect(self, client, userdata, rc):
        """Disconnection callback."""
        print("[Error] Disconnected: rc={} ({})".format(
            rc, mqtt.connack_string(rc)))

    def on_message(self, client, userdata, message):
        """Subscribed message handler."""
        try:
            self.channels[message.topic].messages.put(message.payload)
        except KeyError:
            raise Exception(
                "Received message from topic {} that we shouldn't be "
                "subscribed to.".format(message.topic))

    def open(self, topic):
        """Open new channel."""
        topic = str(topic)

        self.subscribe(topic)
        res = Channel(topic, self)
        self.channels[topic] = res
        return res
