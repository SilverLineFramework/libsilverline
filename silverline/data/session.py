"""All data traces from a specific session."""

import os
import json
import numpy as np
from tqdm import tqdm

from .load import Trace, SplitTrace


class Session:
    """Loader for all data traces from a specific session.

    Parameters
    ----------
    dir : str or str[]
        Base directory for this session. Should contain a `manifest.json`
        and directories file-1, file-2, ... for each trace.
    preload : bool
        Preload SplitTrace.
    """

    _stats = {
        "mean": np.mean,
        "median": np.median,
        "mad": lambda y: np.median(np.abs(y - np.median(y))),
        "std": lambda y: np.sqrt(np.var(y)),
        "n": len,
        "min": np.min,
        "max": np.max
    }

    def __init__(self, dir="data", preload=False):

        if isinstance(dir, str):
            dir = [dir]
        self.dir = dir
        self.preload = preload

        self.manifest = {"runtimes": {}, "modules": {}, "files": {}}
        for d in dir:
            with open(os.path.join(d, "manifest.json")) as f:
                manifest = json.load(f)
                self.manifest["runtimes"].update(manifest["runtimes"])
                self.manifest["modules"].update(manifest["modules"])
                self.manifest["files"].update({
                    k: os.path.join(d, "file-{}".format(v))
                    for k, v in manifest["files"].items()
                })

        self.runtimes = list(set(
            v for _, v in self.manifest["runtimes"].items()))
        self.runtimes.sort()
        self.files = list(self.manifest["files"].keys())
        self.files.sort()
        self.traces = {}

    def _load(self, file):
        if os.path.isdir(file):
            return SplitTrace(
                path=file, manifest=self.manifest, preload=self.preload)
        else:
            return Trace(path=file + ".npz", manifest=self.manifest)

    def get(self, file):
        """Get trace associated with a filename or id.

        Parameters
        ----------
        file : str
            File name or path to trace. If passed as a file name, looks up
            the file name through the manifest. Otherwise, uses the path
            directly.
        """
        file = self.manifest["files"].get(file, file)
        if file not in self.traces:
            try:
                self.traces[file] = self._load(file)
            except FileNotFoundError:
                self.traces[file] = None

        return self.traces[file]

    def stats(self, save=None):
        """Calculate statistics.

        Parameters
        ----------
        save : str or None
            If not None, save results to this file.

        Returns
        -------
        dict(str -> np.array)
            Each entry is a (files x devices) array. Not-present entries are
            listed as 0.
        """
        stats = {
            k: np.zeros((len(self.files), len(self.runtimes)))
            for k in self._stats
        }

        for i, file in enumerate(tqdm(self.files)):
            trace = self.get(file)
            if trace is not None:
                for j, rt in enumerate(self.runtimes):
                    try:
                        y = trace.filter(
                            runtime=rt, keys=["runtime"]
                        ).reset_index()["runtime"][1:-1] / 10**6
                        if len(y) > 0:
                            for k, v in self._stats.items():
                                stats[k][i, j] = v(y)
                    except KeyError:
                        pass
        if save:
            np.savez(save, **stats)
        return stats
