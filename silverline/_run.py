"""Run and test runtime."""

from .client import Client
from .profilers import run_profilers
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser(
        description="Launch module(s), and optionally perform profiling and "
        "send an exit signal.")
    p.add_argument(
        "--runtime", nargs='+', default=["test"],
        help="Target runtime names, uuids, or last 4 characters of uuid.")
    p.add_argument(
        "--path", nargs="+", default=["wasm/apps/helloworld.wasm"],
        help="Target file paths, relative to WASM/WASI base directory")
    p.add_to_parser(
        "client", Client, group="SilverLine Client", exclude=["connect"])
    p.add_to_parser(
        "module", Client.create_module,
        group="Module", exclude=["runtime", "path"])
    p.add_to_parser(
        "profile", run_profilers,
        group="Profiling", exclude=["client", "modules"])
    return p


def _main(args):
    client = Client(**args["client"])
    modules = {}
    for p in args["path"]:
        modules.update(client.create_modules(
            client.infer_runtimes(args["runtime"]), path=p, **args["module"]))
    run_profilers(client, modules, **args["profile"])
    client.loop_stop()
