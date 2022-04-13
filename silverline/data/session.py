"""All data traces from a specific session."""

import os
import json

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
        self.files = list(self.manifest["files"].keys())
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
