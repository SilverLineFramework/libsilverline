"""Stop all runtimes by sending a DELETE_RUNTIME request."""

from .client import Client
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser()
    p.add_argument(
        "--runtime", nargs="+",
        help="Runtimes to stop; if empty, stops all runtimes.", default=[])
    p.add_to_parser("client", Client, group="SilverLine Client")
    return p


def _main(args):
    client = Client(**args["client"])
    runtimes = client.get_runtimes()
    if len(args["runtime"]) > 0:
        for rt in args["runtime"]:
            try:
                print("Stopping runtime {} [{}]".format(rt, runtimes[rt]))
                client.delete_runtime(runtimes[rt], name=rt)
            except KeyError:
                print("Runtime not found: {}".format(rt))
    else:
        print("Stopping all runtimes: {}".format(runtimes))
        for rt, rt_id in runtimes.items():
            print("Stopping runtime {} [{}]".format(rt, rt_id))
            client.delete_runtime(rt_id, name=rt)

    client.loop_stop()
