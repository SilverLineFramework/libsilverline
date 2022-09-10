"""Orchestrator mixins for SilverLine Client."""

import json
import uuid
import requests


class OrchestratorMixin:
    """Orchestrator API mixins."""

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
        self.publish("/".join([self.mqtt_control, target]), payload, qos=2)

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
        self.publish(self.mqtt_control, payload, qos=2)

    def create_module_wasm(
            self, target, name="module", path="wasm/apps/helloworld.wasm",
            argv=[], env=[], period=10000, utilization=0.0,
            fault_crash="ignore"):
        """Create WASM module."""
        module_uuid = str(uuid.uuid4())
        payload = {
            "uuid": module_uuid,
            "name": name,
            "filename": path,
            "filetype": "WA",
            "args": [path] + argv,
            "env": env,
            "fault_crash": fault_crash,
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
            argv=[], env=[], period=10000, utilization=0.0,
            fault_crash="ignore"):
        """Create python module."""
        python = "{t}/rustpython.{t}".format(t="aot" if aot else "wasm")
        module_uuid = str(uuid.uuid4())
        payload = {
            "uuid": module_uuid,
            "name": name,
            "filename": python,
            "filetype": "PY",
            "args": [python, path] + argv,
            "env": env,
            "fault_crash": fault_crash
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
        payload = json.dumps({
            "uuid": str(uuid.uuid4()),
            "type": "arts_req",
            "action": "delete",
            "data": {"uuid": module}
        })
        self.publish(self.mqtt_control, payload, qos=2)

    def create_module(
            self, runtime, name="module", path="wasm/tests/helloworld.wasm",
            argv=[], env=[], filetype="WA", aot=False, period=10000000,
            utilization=0.0, fault_crash="ignore"):
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
        fault_crash : str
            Fault tolerance mode for module crashes; 'ignore' or 'restart'.

        Returns
        -------
        str
            ID of created module.
        """
        kwargs = {
            "name": name, "path": path, "argv": argv, "env": env,
            "period": period, "utilization": utilization,
            "fault_crash": fault_crash
        }
        if filetype == "PY":
            return self.create_module_py(runtime, aot=aot, **kwargs)
        else:
            return self.create_module_wasm(runtime, **kwargs)

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

    def _get_json(self, address):
        """Get JSON from REST API."""
        r = requests.get("{}/{}/".format(self.arts_api, address))
        if r:
            try:
                return json.loads(r.text)
            except Exception as e:
                print(r.text)
                raise e
        return {}

    def get_runtimes(self):
        """Get runtimes from REST API."""
        return self._get_json("runtimes")['runtimes']

    def get_modules(self):
        """Get modules from REST API."""
        return self._get_json("modules")['modules']

    def get_runtime(self, rt):
        """Get runtime full metadata from REST API."""
        return self._get_json("runtimes/{}".format(rt))

    def get_module(self, mod):
        """Get module full metadata from REST API."""
        return self._get_json("modules/{}".format(mod))
