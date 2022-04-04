"""Get status for devices specified in a TSV file."""

import printtools as pt
import pandas as pd
import subprocess
from multiprocessing.pool import ThreadPool

from silverline import parse, parse_args
from silverline.client import Client


def _get_status(row, suffix):
    row = row[1]
    if row['Type'] in {'linux', 'arts'}:
        return subprocess.run(
            ["ping", "-c", "1", "-W", "1", row['Device'] + suffix],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
    else:
        return None


def _show_table(status, runtimes, uuids, targets):
    STATUS_TEXT = {
        True: pt.render("up", pt.GREEN, pt.BOLD, pt.BRIGHT),
        False: pt.render("down", pt.RED, pt.BOLD, pt.BRIGHT),
        None: pt.render("--", pt.BOLD, pt.BRIGHT)
    }
    RUNTIME_TEXT = {
        True: pt.render("running", pt.GREEN, pt.BOLD, pt.BRIGHT),
        False: pt.render("down", pt.RED, pt.BOLD, pt.BRIGHT),
        None: pt.render("n/a", pt.BLUE, pt.BOLD, pt.BRIGHT)
    }

    print("")
    heading = [
        pt.render(h, pt.BOLD)
        for h in ["Node", "Runtime", "UUID"] + list(targets.columns)]
    rows = [list(row) for _, row in targets.iterrows()]

    table = [heading] + [
        [STATUS_TEXT[s], RUNTIME_TEXT[rt], u] + row
        for (s, rt, u, row) in zip(status, runtimes, uuids, rows)
    ]
    pt.table(table, vline=False, heading=True)
    print("")


def status_table(args):
    """Get status for a device table."""
    targets = pd.read_csv(args.manifest, sep='\t')
    print("Pinging {} targets...".format(len(targets)))
    with ThreadPool(processes=len(targets)) as pool:
        status = pool.map(
            lambda x: _get_status(x, args.domain), list(targets.iterrows()))

    print("Fetching runtimes...")
    try:
        arts = SilverLine.from_args(args, connect=False)
        rt_dict = arts.get_runtimes()
        print("Received runtimes: {}".format(rt_dict))
        runtimes = [row["Device"] in rt_dict for _, row in targets.iterrows()]
        uuids = [
            rt_dict.get(row["Device"], "-") for _, row in targets.iterrows()]
    except Exception as e:
        runtimes = [None for _ in targets.iterrows()]
        uuids = ["-" for _ in targets.iterrows()]
        print("No response from ARTS.")

    _show_table(status, runtimes, uuids, targets)


def list_only(args):
    """Get runtimes from ARTS only."""
    print("Fetching runtimes...")
    try:
        arts = Client.from_args(args, connect=False)
        runtime_dict = arts.get_runtimes()
        print("Received runtimes: {}".format(runtime_dict))
    except Exception as e:
        print("No response from ARTS.")


if __name__ == '__main__':

    args = parse_args(parse.mqtt, parse.http, parse.cluster)
    try:
        status_table(args)
    except FileNotFoundError:
        print("Could not find manifest file: {}.".format(args.manifest))
        list_only(args)
