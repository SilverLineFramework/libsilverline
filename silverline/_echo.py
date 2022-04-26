"""Send echo to orchestrator."""

from .client import Client
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser()
    p.add_to_parser(
        "client", Client, group="SilverLine Client", exclude=["connect"])
    p.add_to_parser("echo", Client.echo, group="Echo")
    return p


def _main(args):
    client = Client(**args["client"])
    client.echo(**args["echo"])
    client.loop_stop()