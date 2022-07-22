"""Stop runtimes by sending a DELETE_RUNTIME request."""

from .client import Client
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser(
        description="Send stop signal to specified runtimes, or all runtimes "
        "by default.")
    p.add_argument(
        "--runtime", nargs="+", default=[],
        help="Runtimes to stop; if empty, stops all runtimes. Runtimes can be "
        "specified by name, UUID, or last 4 characters of UUID.")
    p.add_to_parser(
        "client", Client, group="SilverLine Client", exclude=["connect"])
    return p


def _main(args):
    client = Client(**args["client"])
    if len(args["runtime"]) > 0:
        runtimes = client.infer_runtimes(args["runtime"])
        for rt in runtimes:
            print("Stopping runtime {}".format(rt))
            client.delete_runtime(rt)
    else:
        runtimes = client.get_runtimes()
        print("Stopping all runtimes:")
        for rt in runtimes:
            print("Stopping runtime {} [{}]".format(rt["name"], rt["uuid"]))
            client.delete_runtime(rt["uuid"])

    client.loop_stop()
