"""Stop all runtimes by sending a DELETE_RUNTIME request."""

from .client import Client
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser()
    p.add_argument(
        "--runtime", nargs="+",
        help="Runtimes to stop; if empty, stops all runtimes.", default=[])
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
        print("Stopping all runtimes: {}".format(runtimes))
        for rt_id, rt in runtimes.items():
            print("Stopping runtime {} [{}]".format(rt, rt_id))
            client.delete_runtime(rt_id, name=rt)

    client.loop_stop()
