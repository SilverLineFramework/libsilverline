"""SilverLine system interface."""

import json
import uuid
import requests
import ssl

from threading import Semaphore
import paho.mqtt.client as mqtt


class Client(mqtt.Client):
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
    """

    def __init__(
            self, mqtt="localhost", mqtt_port=1883, pwd="mqtt_pwd.txt",
            mqtt_username="cli", use_ssl=False, http="localhost",
            http_port=8000, connect=True):

        self.callbacks = {}
        self.arts_api = "http://{}:{}/arts-api/v1".format(http, http_port)

        super().__init__("Benchmarking")

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

    def create_module(
            self, runtime, name="module", path="wasm/apps/helloworld.wasm",
            argv=[], env=[], filetype="PY", aot=False):
        """Create module.

        Parameters
        ----------
        runtime : str
            Runtime ID.
        name : str
            Module name.
        path : str
            Filepath to module binary/script, relative to the WASM/WASI base
            directory used by the runtime.
        argv : str[]
            Argument passthrough to the module.
        env : str[]
            Environment variables to set.
        filetype : str
            Module type; PY or WA.
        aot : bool
            If running a python module, whether to use aot or interpreted.

        Returns
        -------
        str
            ID of created module.
        """
        if filetype == "PY":
            return self.create_module_py(
                runtime, name=name, path=path, aot=aot, argv=argv, env=env)
        else:
            return self.create_module_wasm(
                runtime, name=name, path=path, argv=argv, env=env)

    def create_modules(
            self, runtimes, path="wasm/apps/helloworld.wasm", **kwargs):
        """Create multiple runtimes; returns UUID as a dictionary."""
        return {
            (rt, path): self.create_module(rt, path=path, **kwargs)
            for rt in runtimes
        }

    def create_modules_name(self, runtimes, **kwargs):
        """Create modules specified by name instead of UUID."""
        rt_list = self.get_runtimes()

        def _lookup(rt):
            try:
                return rt_list(rt)
            except KeyError:
                return ValueError("Runtime not found: {}".format(rt))

        return self.create_modules([_lookup(rt) for rt in runtimes], **kwargs)

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
