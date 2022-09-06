"""Save profiling data."""

import json

from .client import Client
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser(description="Save data collection state.")
    p.add_to_parser(
        "client", Client, group="SilverLine Client", exclude=["connect"])
    p.add_argument(
        "--metadata", help="Message metadata (JSON encoded)",
        default='{"metadata": null}')
    return p


def _main(args):
    client = Client(**args["client"])
    client.save(json.loads(args["metadata"]))
    client.loop_stop()
