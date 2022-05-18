"""List running runtimes and modules."""

import printtools as pt

from .client import Client
from .parse import ArgumentParser


def _parse():
    p = ArgumentParser()
    p.add_to_parser(
        "client", Client, group="SilverLine Client", exclude=["connect"])
    p.add_argument(
        "--style", default="full", help="List style (full or short)")
    return p


def _emph(x):
    return pt.render("{}".format(x), pt.BOLD, pt.BLUE, pt.BR)


def _fmt_module(mod):
    return "{}:{}".format(mod['uuid'][-4:], mod['name'])


def _short(runtimes):
    rows = [["uuid:name", "modules"]]
    for rt in runtimes:
        module_uuids = [_fmt_module(mod) for mod in rt['children']]
        if module_uuids:
            module_uuids = " ".join(module_uuids)
        else:
            module_uuids = "--"

        rows.append([
            _emph("{}:{}".format(rt['uuid'][-4:], rt['name'])), module_uuids])

    pt.table(rows, vline=False)


def _full(runtimes):
    for rt in runtimes:
        pt.print("{}:{}".format(_emph(rt['uuid']), rt['name']))
        for mod in rt['children']:
            pt.print("    {}:{} ({})".format(
                _emph(mod['uuid'][-4:]), mod['name'], mod['filename']))


def _main(args):
    client = Client(connect=False, **args["client"])
    runtimes = client.get_runtimes(by_name=False)

    if args["style"] == "short":
        _short(runtimes)
    else:
        _full(runtimes)
