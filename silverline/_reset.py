"""Reset profiling."""

from .client import Client
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser()
    p.add_to_parser(
        "client", Client, group="SilverLine Client", exclude=["connect"])
    return p


def _main(args):
    client = Client(**args["client"])
    client.reset()
    client.loop_stop()
