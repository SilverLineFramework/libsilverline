"""Run and test runtime."""

from silverline import _run, parse

if __name__ == '__main__':
    args = parse.parse_args(parse.http, parse.mqtt, parse.benchmark)
    _run._main(args)
