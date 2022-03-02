"""Main runtime."""

import uuid
import json

from channels import Channels


class Registration:
    """Runtime registration."""

    def __init__(
            self, rt_id="", name="", apis=[], realm="realm",
            registration="proc/reg", keepalive="proc/keepalive",
            profile="proc/profile", control="proc/control"):

        self.rt_id = rt_id
        self.name = name
        self.apis = apis
        self.realm = realm
        self.registration = "/".join([realm, registration])
        self.keepalive = "/".join([realm, keepalive])
        self.profile = "/".join([realm, profile])
        self.control = "/".join([realm, control, rt_id])

    def _create_delete_runtime_data(self):
        """Create/delete runtime body."""
        return {
            "type": "runtime",
            "uuid": self.rt_id,
            "name": self.name,
            "runtime_type": "special",
            "apis": [self.apis],
        }

    def create_msg(self):
        """Create runtime message."""
        return json.dumps({
            "object_id": str(uuid.uuid4()),
            "action": "create",
            "type": "arts_req",
            "data": self._create_delete_runtime_data()
        })

    def delete_msg(self):
        """Delete runtime message for MQTT will."""
        return json.dumps({
            "object_id": str(uuid.uuid4()),
            "action": "delete",
            "type": "arts_req",
            "data": self._create_delete_runtime_data()
        })


class Runtime:
    """Main runtime object.

    Keyword Args
    ------------
    rt_id : str or None
        Runtime ID; if None, generates a random uuid.uuid4().
    name : str
        Runtime name.
    apis : str[]
        List of supported runtime APIs; should be custom.
    mqtt_args : dict
        Passthrough to Channels.
    topics : str
        Passthrough to Registration topic controls.
    timeout : int
        Timeout in milliseconds for runtime registration.
    """

    def __init__(
            self, rt_id=None, name="Special Runtime", apis=["special"],
            mqtt_args={}, topics={}, timeout=5000):
        if rt_id is None:
            rt_id = str(uuid.uuid4())
        self.rt_id = rt_id
        self.name = name
        self.apis = apis
        self.timeout = timeout

        reg = Registration(rt_id=rt_id, name=name, apis=apis, **topics)
        self.channels = Channels(**mqtt_args)
        self.channels.will_set(reg.registration, reg.delete_msg())

        reg_channel = self.channels.open(reg.registration)
        self.channels.publish(reg.registration, reg.create_msg())
        if not self._connect(reg_channel):
            raise Exception("Could not register with ARTS.")
        reg_channel.close()

        self.control = self.channels.open(reg.control)
        self.profile = self.channels.open(reg.profile)

    def _connect(self, reg_channel):
        """Connect to ARTS."""
        for _ in range(self.timeout):
            msg = reg_channel.poll(1)
            if msg is not None:
                return True
        return False
