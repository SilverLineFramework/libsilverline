"""Stop modules by sending a DELETE_MODULE request."""

from .client import Client
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser(
        description="Send DELETE_RUNTIME signal to specified module.")
    p.add_argument(
        "--module", nargs="+", default=[],
        help="Modules to stop. Modules can be specified by name, UUID, or "
        "last 4 characters of UUID.")
    p.add_to_parser(
        "client", Client, group="SilverLine Client", exclude=["connect"])
    return p


def _main(args):
    client = Client(**args["client"])
    modules = client.infer_modules(args["module"])
    for mod in modules:
        client.delete_module(mod)
    client.loop_stop()
