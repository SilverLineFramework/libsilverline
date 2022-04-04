"""SilverLine system interface."""

import json
import uuid
import requests
import ssl

from threading import Semaphore
import paho.mqtt.client as mqtt


class Client(mqtt.Client):
    """SilverLine Interface.

    Keyword Args
    ------------
    mqtt : str
        MQTT host server address.
    mqtt_port : int
        MQTT host server port.
    http : str
        Orchestrator HTTP server address.
    http_port : int
        Orchestrator HTTP server port.
    pwd : str
        MQTT password file
    username : str
        MQTT username
    ssl : bool
        Whether to use SSL.
    connect : bool
        If False, don't connect to MQTT.
    """

    def __init__(
            self, mqtt="localhost", mqtt_port=1883, pwd="mqtt_pwd.txt",
            username="cli", use_ssl=False, http="localhost", http_port=8000,
            connect=True):

        self.callbacks = {}
        self.arts_api = "http://{}:{}/arts-api/v1".format(http, http_port)

        super().__init__("Benchmarking")

        if connect:
            self.semaphore = Semaphore()
            self.semaphore.acquire()

            with open(pwd, 'r') as f:
                passwd = f.read().rstrip('\n')
            self.username_pw_set(username, passwd)
            if use_ssl:
                self.tls_set(cert_reqs=ssl.CERT_NONE)
            self.connect(mqtt, mqtt_port, 60)

            # Waiting for on_connect to release
            self.loop_start()
            self.semaphore.acquire()

    @classmethod
    def from_args(cls, args, connect=True):
        """Construct from namespace such as ArgumentParser."""
        return cls(
            mqtt=args.mqtt, mqtt_port=args.mqtt_port, pwd=args.pwd,
            username=args.username, use_ssl=args.ssl, http=args.http,
            http_port=args.http_port, connect=connect)

    def on_connect(self, mqttc, obj, flags, rc):
        """On connect callback."""
        print("[Setup] Connected: rc={} ({})".format(
            rc, mqtt.connack_string(rc)))
        if self.semaphore is not None:
            self.semaphore.release()

    def on_disconnect(self, client, userdata, rc):
        """Disconnection callback."""
        print("[Error] Disconnected: rc={} ({})".format(
            rc, mqtt.connack_string(rc)))

    def delete_runtime(self, target, name="test"):
        """Instruct runtime to exit."""
        payload = json.dumps({
            "object_id": str(uuid.uuid4()),
            "action": "delete",
            "type": "arts_req",
            "data": {
                "type": "runtime",
                "uuid": target,
                "name": name
            }
        })
        self.publish("realm/proc/control/{}".format(target), payload)

    def _create_module(self, data, target):
        """Create Module helper function."""
        payload = json.dumps({
            "object_id": str(uuid.uuid4()),
            "action": "create",
            "type": "arts_req",
            "data": {
                "type": "module",
                "parent": {"uuid": target},
                **data
            }
        })
        self.publish("realm/proc/control", payload)

    def create_module_wasm(
            self, target, name="module",
            path="wasm/apps/helloworld.wasm", argv=[], env=[]):
        """Create WASM module."""
        module_uuid = str(uuid.uuid4())
        self._create_module({
            "uuid": module_uuid,
            "name": name,
            "filename": path,
            "filetype": "WA",
            "args": [path] + argv,
            "env": env,
        }, target)
        return module_uuid

    def create_module_py(
            self, target, name="module", aot=False, path="python/pinata.py",
            argv=[], env=[]):
        """Create python module."""
        python = "{t}/rustpython.{t}".format(t="aot" if aot else "wasm")
        module_uuid = str(uuid.uuid4())
        self._create_module({
            "uuid": module_uuid,
            "name": name,
            "filename": python,
            "filetype": "PY",
            "args": [python, path] + argv,
            "env": env
        }, target)
        return module_uuid

    def register_callback(self, topic, callback):
        """Subscribe to topic and register callback for that topic."""
        self.subscribe(topic)
        self.callbacks[topic] = callback

    def on_message(self, client, userdata, message):
        """Subscribed message handler."""
        topic = str(message.topic)
        try:
            self.callbacks[topic](message.payload)
        except KeyError:
            print("[Warning] topic without handler: {}".format(topic))

    def get_runtimes(self):
        """Get runtimes from REST API."""
        r = requests.get("{}/runtimes/".format(self.arts_api))
        try:
            res = json.loads(r.text)
        except Exception as e:
            print(r.text)
            raise e

        return {rt['name']: rt['uuid'] for rt in res}
