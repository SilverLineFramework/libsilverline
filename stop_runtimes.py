"""Stop all runtimes by sending a DELETE_RUNTIME request."""

from silverline import stop_runtimes, parse, parse_args


if __name__ == '__main__':
    parse = parse_args(stop_runtimes._parse, parse.http, parse.mqtt)
    stop_runtimes._main(parse)
