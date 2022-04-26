"""Send echo to orchestrator."""

from silverline import _echo


if __name__ == '__main__':
    _echo._main(_echo._parse().parse_args())
