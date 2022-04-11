"""Stop all runtimes by sending a DELETE_RUNTIME request."""

from silverline import _stop_runtimes

if __name__ == '__main__':
    _stop_runtimes._main(_stop_runtimes._parse().parse_args())
