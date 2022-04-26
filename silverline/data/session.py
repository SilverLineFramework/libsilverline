"""All data traces from a specific session."""

import os
import json
import numpy as np
from matplotlib import pyplot as plt
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

    def _iter_grid(self, axs, func):
        for file, row in zip(self.files, axs):
            trace = self.get(file)
            for rt, ax in zip(self.runtimes, row):
                try:
                    func(ax, trace, rt)
                except Exception as e:
                    print("Error at ({}, {}): {}".format(file, rt, e))
            row[0].set_ylabel(file.split("/")[-1])

    def plot_grid(
            self, keys=["cpu_time"], multiplier=1 / 10**6, limit_mad=5.,
            limit_rel=0.05, save="test.png", mode='trace', dpi=100,
            xaxis="index"):
        """Plot execution traces or histogram.

        Parameters
        ----------
        keys : str[]
            Keys to plot, i.e. cpu_time, wall_time, etc.
        multiplier : float
            Multiplier to apply to the value being plotted (unit conversion)
        limit_mad : float
            Y-axis limits for trace plots, specified relative to the MAD. If 0,
            no limits are applied.
        limit_rel : float
            Minimum upper and lower margin, specified relative to the median.
        save : str
            If passed, save plot using plt.savefig and close immediately.
        mode : str
            Plot mode; can be 'trace' or 'hist'.
        dpi : int
            DPI to save the plot as. Large DPI (>100) may cause python to be
            killed due to OOM.
        xaxis : str
            X-axis data. Can be 'index' or 'time'.
        """
        fig, axs = plt.subplots(
            len(self.files), len(self.runtimes),
            figsize=(2 * len(self.runtimes), 2 * len(self.files)))

        def _inner(ax, trace, rt):
            if xaxis == 'index':
                df = trace.filter(runtime=rt, keys=keys).reset_index()
                x = np.arange(len(df))
            else:
                df = trace.filter(
                    runtime=rt, keys=keys + ["start_time"]).reset_index()
                x = (df["start_time"][1:-1] - df["start_time"][0]) / 10**9

            yy = np.array([df[k][1:-1] * multiplier for k in keys])
            mm = np.median(yy, axis=1)

            if mode == 'trace':
                if xaxis == 'index':
                    ax.plot(yy.T, linewidth=0.6)
                else:
                    ax.plot(x, yy.T, linewidth=0.6)

                if limit_mad != 0:
                    mads = np.median(np.abs(yy - mm.reshape(-1, 1)), axis=1)
                    radius = np.maximum(mads * limit_mad, limit_rel * mm)
                    ax.set_ylim(np.min(mm - radius), np.max(mm + radius))

            elif mode == 'hist':
                c = np.mean(mm)
                for y in yy:
                    ax.hist(y, bins=np.linspace(0.5 * c, c * 1.5, 50))

        self._iter_grid(axs, _inner)

        for ax, rt in zip(axs[-1], self.runtimes):
            ax.set_xlabel(rt)
        for ax, rt in zip(axs[0], self.runtimes):
            ax.set_title(rt)

        fig.tight_layout(h_pad=0, w_pad=0)

        if save != "":
            fig.savefig(save, dpi=dpi)
            plt.close(fig)
        else:
            return fig, axs
