"""All data traces from a specific session."""

import os
import json

from .load import Trace


class Session:
    """Loader for all data traces from a specific session.

    Parameters
    ----------
    dir : str
        Base directory for this session. Should contain a `manifest.json`
        and directories file-1, file-2, ... for each trace.
    """

    def __init__(self, dir="data"):

        self.dir = dir
        with open(os.path.join(dir, "manifest.json")) as f:
            self.manifest = json.load(f)
        self.runtimes = list(set(
            v for _, v in self.manifest["runtimes"].items()))
        self.files = [v for _, v in self.manifest["files"]]

        self.traces = {}

    def get(self, file):
        """Get trace associated with a filename or id.

        Parameters
        ----------
        file : str or int
            File name or id. If str, looks up the file id through the manifest.
            If int, uses as a file id directly.
        """
        if isinstance(file, str):
            file = self.manifest["files"][file]

        if file not in self.traces:
            try:
                self.traces[file] = Trace(
                    dir=os.path.join(self.dir, "file-{}".format(file)),
                    manifest=self.manifest)
            except FileNotFoundError:
                self.traces[file] = None

        return self.traces[file]

    def matrix(self, func, mat, **kwargs):
        """Apply function to a runtimes x files matrix."""
        for i, rt in self.runtimes:
            for j, file in self.files:
                mat[i][j] = func(mat, rt, file, **kwargs)
