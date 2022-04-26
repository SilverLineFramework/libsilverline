"""Generate data plots."""

from .data import Session
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser()
    p.add_argument(
        "path", nargs='+', default=['data'],
        help="Directories to plot data from; must be in orchestrator format.")
    p.add_argument(
        "--keys", nargs='+', default=['cpu_time'],
        help="Keys to plot, i.e. cpu_time, wall_time, etc.")
    p.add_to_parser("plot", Session.plot_grid, group="plot", exclude='keys')
    return p


def _main(args):
    dataset = Session(args["path"])
    dataset.plot_grid(keys=args["keys"], **args["plot"])
