"""Run and test runtime."""

from libsilverline import _reset

if __name__ == '__main__':
    _reset._main(_reset._parse().parse_args())
