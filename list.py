"""List running runtimes and modules."""

from silverline import _list

if __name__ == '__main__':
    _list._main(_list._parse().parse_args())

