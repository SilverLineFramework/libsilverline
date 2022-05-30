"""Stop modules by sending a DELETE_MODULE request."""

from silverline import _stop_modules


if __name__ == '__main__':
    _stop_modules._main(_stop_modules._parse().parse_args())
