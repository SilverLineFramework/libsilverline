"""Run and test runtime."""

from silverline import run, parse_args, parse

if __name__ == '__main__':
    args = parse_args(parse.http, parse.mqtt, parse.benchmark)
    run._main(args)
