"""Data loader."""

import os
import numpy as np
import pandas as pd
import uuid


class Trace:
    """Loader corresponding to the DataStore class for profiling data.

    Note that numpy arrays are 'lazy-loaded', and do not actually populate in
    memory until referenced.

    Parameters
    ----------
    path : str
        Path for this data trace. Should be a .npz file.
    manifest : dict
        Optional manifest created by the orchestrator; should have "runtimes"
        and "modules" id-name maps. If passed, will create dictionaries with
        name-id lookups.
    """

    def __init__(self, path="data", manifest=None):

        self.npz = np.load(path)
        self.size = self.npz["size"]
        self.data = {k: v for k, v in self.npz.items() if k != 'size'}
        self.data["runtime_id"] = self._to_uuid_str(self.data["runtime_id"])
        self.data["module_id"] = self._to_uuid_str(self.data["module_id"])

        if manifest:
            self.runtimes = self._name_key("runtime_id", manifest["runtimes"])
            self.modules = self._name_key("module_id", manifest["modules"])
            self.manifest = {
                "runtime": self.runtimes,
                "modules": self.modules
            }

    def _name_key(self, key, manifest):
        return {
            manifest[key]: key
            for key in np.unique(self._get_array(key))
        }

    @staticmethod
    def _to_uuid_str(column):
        return [str(uuid.UUID(bytes=x.tobytes())) for x in column]

    def arrays(self, keys=None):
        """Load as dictionary of arrays."""
        if not keys:
            return self.data
        else:
            return {k: self.data[k] for k in keys}

    def dataframe(self, keys=None):
        """Load as dataframe."""
        return pd.DataFrame(self.arrays(keys=keys))

    def filter(self, keys=None, **kwargs):
        """Load dataframe with given filters.

        Special Keys: if `runtime=` or `module=` are passed, the result will
        be filtered by their name instead. Use `runtime_id` and `module_id`
        to look up their UUID directly.
        """
        if keys is not None:
            keys += ["runtime_id", "module_id"]

        df = self.dataframe(keys=keys)
        for k, v in kwargs.items():
            if k in self.manifest:
                v = self.manifest[k][v]
                k = k + "_id"
            df = df[df[k] == v]
        return df


class SplitTrace(Trace):
    """Loader corresponding to the DataStore class for profiling data.

    Note that numpy arrays are 'lazy-loaded', and do not actually populate in
    memory until referenced.

    Parameters
    ----------
    path : str
        Base directory for this data trace. Should contain files
        chunk_1.npz, chunk_2.npz, ...
    manifest : dict
        Optional manifest created by the orchestrator; should have "runtimes"
        and "modules" id-name maps. If passed, will create dictionaries with
        name-id lookups.
    """

    def __init__(self, path="data", manifest=None):

        self.sources = os.listdir(path)
        self.sources.sort()
        self.chunks = [np.load(os.path.join(path, s)) for s in self.sources]
        self.size = sum(s['size'] for s in self.chunks)
        self.data = {}

        if manifest:
            self.runtimes = self._name_key("runtime_id", manifest["runtimes"])
            self.modules = self._name_key("module_id", manifest["modules"])
            self.manifest = {
                "runtime": self.runtimes,
                "modules": self.modules
            }

    def _aggregate(self, k):
        v = self.chunks[0][k]
        res = np.zeros([self.size] + list(v.shape)[1:], dtype=v.dtype)
        idx = 0
        for c in self.chunks:
            size = c['size']
            res[idx:idx + size] = c[k][:size]
            idx += size
        return res

    def _get_array(self, k):
        if k not in self.data:
            self.data[k] = self._aggregate(k)
            if k in {'module_id', 'runtime_id'}:
                self.data[k] = self._to_uuid_str(self.data[k])

        return self.data[k]

    def arrays(self, keys=None):
        """Load as dictionary of arrays."""
        if not keys:
            keys = [k for k in self.chunks[0].keys() if k != 'size']

        return {k: self._get_array(k) for k in keys}

    def merge(self, dst):
        """Merge to a single .npz file."""
        data = self.arrays()
        data['size'] = self.size
        data['runtime_id'] = self._aggregate("runtime_id")
        data['module_id'] = self._aggregate("moudle_id")
        np.savez(dst, **data)
