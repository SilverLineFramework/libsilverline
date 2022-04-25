"""Generate data plots."""

from .data import Session
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser()
    p.add_argument(
        "path", nargs='+', default=['data'],
        help="Directories to plot data from; must be in orchestrator format.")
    p.add_to_parser("plot", Session.plot_grid, group="plot")
    return p


def _main(args):
    dataset = Session(args["path"])
    dataset.plot_grid(**args["plot"])
