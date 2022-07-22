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
        self.arts_api = "http://{}:{}/api".format(http, http_port)

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
        """On connect callback."""
        if self.semaphore is not None:
            self.semaphore.release()

    def on_disconnect(self, client, userdata, rc):
        """Disconnection callback."""
        print("Disconnected: rc={} ({})".format(
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
                "parent": target,
                **data
            }
        })
        self.publish("realm/proc/control", payload)

    def create_module_wasm(
            self, target, name="module", path="wasm/apps/helloworld.wasm",
            argv=[], env=[], period=10000, utilization=0.0):
        """Create WASM module."""
        module_uuid = str(uuid.uuid4())
        payload = {
            "uuid": module_uuid,
            "name": name,
            "filename": path,
            "filetype": "WA",
            "args": [path] + argv,
            "env": env,
        }
        if utilization > 0:
            payload["resources"] = {
                "period": period,
                "runtime": int(utilization * period)
            }
        self._create_module(payload, target)
        return module_uuid

    def create_module_py(
            self, target, name="module", aot=False, path="python/pinata.py",
            argv=[], env=[], period=10000, utilization=0.0):
        """Create python module."""
        python = "{t}/rustpython.{t}".format(t="aot" if aot else "wasm")
        module_uuid = str(uuid.uuid4())
        payload = {
            "uuid": module_uuid,
            "name": name,
            "filename": python,
            "filetype": "PY",
            "args": [python, path] + argv,
            "env": env
        }
        if utilization > 0:
            payload["resources"] = {
                "period": period,
                "runtime": int(utilization * period)
            }
        self._create_module(payload, target)
        return module_uuid

    def delete_module(self, module):
        """Delete module."""
        self.publish("realm/proc/control", json.dumps({
            "uuid": str(uuid.uuid4()),
            "type": "arts_req",
            "action": "delete",
            "data": {"uuid": module}
        }))

    def create_module(
            self, runtime, name="module", path="wasm/tests/helloworld.wasm",
            argv=[], env=[], filetype="WA", aot=False, period=10000000,
            utilization=0.0):
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
        period : int
            Period for sched_deadline, in nanoseconds.
        utilization : float
            Utilization for sched_deadline. If 0.0, uses CFS.

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
                runtime, name=name, path=path, argv=argv, env=env,
                period=period, utilization=utilization)

    def create_modules(
            self, runtimes, path="wasm/apps/helloworld.wasm", **kwargs):
        """Create multiple modules; returns UUID as a dictionary."""
        return {
            (rt, path): self.create_module(rt, path=path, **kwargs)
            for rt in runtimes
        }

    def _infer(self, mode, query):
        res = []
        for q in query:
            resp = self._get_json("{}/{}".format(mode, q))
            if resp:
                res.append(resp['uuid'])
        return res

    def infer_runtimes(self, runtimes):
        """Infer runtime UUIDs.

        Accepted aliases:
          - name; undefined behavior if multiple runtimes have same name
          - last 4 characters of string-encoded UUID
          - full UUID.
        """
        return self._infer("runtimes", runtimes)

    def infer_modules(self, modules):
        """Infer module UUIDs."""
        return self._infer("modules", modules)

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

    def _get_json(self, address):
        """Get JSON from REST API."""
        r = requests.get("{}/{}/".format(self.arts_api, address))
        try:
            return json.loads(r.text)
        except Exception as e:
            print(r.text)
            raise e

    def get_runtimes(self):
        """Get runtimes from REST API."""
        return self._get_json("runtimes")['runtimes']

    def get_modules(self):
        """Get modules from REST API."""
        return self._get_json("modules")['modules']
