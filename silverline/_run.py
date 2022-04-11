"""Run and test runtime."""

from .client import Client, run_profilers
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser()
    p.add_argument(
        "--runtime", nargs='+', help="Target runtime names.", default=["test"])
    p.add_argument(
        "--path", nargs="+", default=["wasm/apps/helloworld.wasm"],
        help="Target file paths, relative to WASM/WASI base directory")
    p.add_to_parser("client", Client, group="SilverLine Client")
    p.add_to_parser(
        "module", Client.create_module,
        group="Module", exclude=["runtime", "path"])
    p.add_to_parser(
        "profile", run_profilers,
        group="Profiling", exclude=["client", "modules"])
    return p.parse_args()


def _main(args):
    client = Client(**args["client"])
    modules = {}
    for p in args.path:
        modules.update(client.create_modules_name(
            args["runtime"], path=p, **args["module"]))
    run_profilers(client, modules, **args["profile"])
    client.loop_stop()
