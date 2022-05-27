"""All data traces from a specific session."""

import os
import numpy as np
import json
import pandas as pd
from matplotlib import pyplot as plt

from tqdm import tqdm

from .load import Trace


class Session:
    """Loader for all data traces from a specific session.

    Parameters
    ----------
    dir : str
        Base directory for this session.
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

    def __init__(self, dir="data"):

        if isinstance(dir, list):
            dir = dir[0]

        self.dir = dir
        self.manifest = pd.read_csv(os.path.join(dir, "manifest.csv"))
        with open(os.path.join(dir, "metadata.json")) as f:
            self.metadata = json.load(f)

        self.files = self.manifest['file'].unique()
        self.files.sort()
        self.runtimes = self.manifest['runtime'].unique()
        self.runtimes.sort()

    def filter(self, **kwargs):
        """Filter manifest."""
        df = self.manifest
        for k, v in kwargs.items():
            df = df[df[k] == v]
        return df

    def _get(self, row):
        return Trace(os.path.join(self.dir, row['file_id'], row['module_id']))

    def get(self, **kwargs):
        """Look up trace. If more than one match, returns the first."""
        df = self.filter(**kwargs)
        if len(df) == 0:
            return None
        else:
            return self._get(df.iloc[0])

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
        stats["files"] = np.array(self.files)
        stats["runtimes"] = np.array(self.runtimes)

        for i, file in enumerate(tqdm(self.files)):
            for j, rt in enumerate(self.runtimes):
                trace = self.get(file=file, runtime=rt)
                y = trace.arrays(keys=["cpu_time"])['cpu_time']
                if y:
                    for k, v in self._stats.items():
                        stats[k][i, j] = v(y)
        if save:
            np.savez(save, **stats)
        return stats

    def plot_grid(
            self, keys=["cpu_time"], multiplier=1 / 10**6, limit_mad=5.,
            limit_rel=0.05, save="test.png", mode='trace', dpi=100,
            hist_width=0.5, xaxis="index"):
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
        hist_width : float
            Radius of histogram relative to mean. If 0., no limits are applied.
        xaxis : str
            X-axis data. Can be 'index' or 'time'.
        """

        def _inner(ax, trace):
            if xaxis == 'index':
                df = trace.dataframe(keys=keys)
                x = np.arange(len(df))
            else:
                df = trace.dataframe(keys=keys + ["start_time"])
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
                    if hist_width > 0:
                        ax.hist(y, bins=np.linspace(
                            hist_width * c, c * (1 + hist_width), 50))
                    else:
                        ax.hist(y, bins=50)

        fig, axs = plt.subplots(
            len(self.files), len(self.runtimes),
            figsize=(2.25 * len(self.runtimes), 2 * len(self.files)))

        for row, file in zip(axs, self.files):
            for ax, rt in zip(row, self.runtimes):
                trace = self.get(file=file, runtime=rt)
                if trace:
                    _inner(ax, trace)
            row[0].set_ylabel(file.split('/')[-1])

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
