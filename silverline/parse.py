"""Base argparse args."""

import json
import sys
from argparse import ArgumentParser


def benchmark(parser):
    """Args for benchmark spawning."""
    # Target
    g = parser.add_argument_group("Benchmark Options")
    g.add_argument("--type", help="PY or WA", default="WA")
    g.add_argument(
        "--path", nargs='+', help="File path(s) to execute",
        default=["wasm/test/helloworld.wasm"])
    g.add_argument(
        "--argv", nargs='+', help="Module argv passthrough", default=[])
    g.add_argument(
        "--runtime", nargs='+', help="Target runtime names", default=["test"])

    # Python only args
    g.add_argument(
        "--env", nargs='+', help="Module environment variables", default=[])
    g.add_argument(
        "--aot", help="Use AOT python for python benchmarks",
        dest="aot", action="store_true")
    g.set_defaults(aot=False)

    # Profiling
    g.add_argument(
        "--mode", help="Profiling mode (passive, active, timed)",
        default="passive")
    g.add_argument(
        "--time", help="Total time limit (seconds) for timed profiling mode",
        type=float, default=60.)
    g.add_argument(
        "--mean_size", default=1000, type=float,
        help="Prior mean message size (used as input to dirichlet process)")
    g.add_argument(
        "--alpha", default=1, type=float,
        help="Dirichlet Process \"new table\" parameter alpha")
    g.add_argument(
        "--n", default=100, type=int,
        help="Number of iterations to test for active profiling mode")
    g.add_argument(
        "--delay", default=0.1, type=float,
        help="Delay between iterations for active/timed profiling mode")


def mqtt(parser):
    """Args for MQTT connection."""
    g = parser.add_argument_group("MQTT Options")
    g.add_argument("--mqtt", help="MQTT Host address", default="localhost")
    g.add_argument("--mqtt_port", help="MQTT port", default=1883, type=int)
    g.add_argument("--username", help="Username", default="cli")
    g.add_argument("--pwd", help="Password file", default="mqtt_pwd.txt")
    g.add_argument("--ssl", help="Use SSL (mqtt-secure)", action="store_true")
    g.set_defaults(ssl=False)


def http(parser):
    """Args for HTTP interface."""
    g = parser.add_argument_group("HTTP Options")
    g.add_argument(
        "--http", help="Orchestrator HTTP hostname", default="localhost")
    g.add_argument("--http_port", help="Orchestrator HTTP port", default=8000)


def cluster(parser):
    """Args for Cluster status and manifest."""
    g = parser.add_argument_group("Cluster Options")
    g.add_argument(
        "--manifest", help="Device specification .tsv file",
        default="devices.tsv")
    g.add_argument(
        "--domain", help="Cluster hostname domain suffix",
        default=".arena.andrew.cmu.edu")


def _get_cfg():
    for arg, next in zip(sys.argv[:-1], sys.argv[1:]):
        if arg == '--config':
            with open(next) as f:
                return json.load(f)
    return {}


def parse_args(*groups, desc=None):
    """Make argument parser."""
    parser = ArgumentParser(description=desc)
    for g in groups:
        g(parser)
    parser.add_argument(
        "--config", help=(
            "Config file to load; priority is (1) explicitly passed args, "
            "(2) config file, (3) defaults"))
    parser.set_defaults(**_get_cfg())
    args = parser.parse_args()

    return args
