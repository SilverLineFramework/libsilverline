"""Stop all runtimes by sending a DELETE_RUNTIME request."""

from silverline import _stop_runtimes
from silverline import parse, parse_args


if __name__ == '__main__':
    parse = parse_args(_stop_runtimes._parse, parse.http, parse.mqtt)
    _stop_runtimes._main(parse)
