"""Run and test runtime."""

from silverline import _run, parse
from utils import parse_args

if __name__ == '__main__':
    args = parse_args(parse.http, parse.mqtt, parse.benchmark)
    _run._main(args)
