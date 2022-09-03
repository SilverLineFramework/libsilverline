"""Run and test runtime."""

from libsilverline import _run

if __name__ == '__main__':
    _run._main(_run._parse().parse_args())
