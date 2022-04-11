"""Inspect function signature for parsing."""

import inspect
import argparse
from docstring_parser import parse, DocstringStyle


class ArgumentParser(argparse.ArgumentParser):
    """Extension of ArgumentParser supporting addition through inspection."""

    def __init__(self, *args, **kwargs):

        self._group_names = {}
        self._arg_names = []
        super().__init__(*args, **kwargs)

    def _add_arg(self, parser, pdoc, psig):
        if psig:
            default = psig.default
            dtype = type(default)
        else:
            default = None
            dtype = str
        parser.add_argument(
            "--{}".format(pdoc.arg_name), type=dtype,
            help=pdoc.description.replace("\n", " "), default=default)
        return pdoc.arg_name

    def add_argument(self, *args, **kwargs):
        """Add argument to parser."""
        if args != ('-h', '--help'):
            self._arg_names += [
                a.lstrip('--') for a in args if a.startswith('--')]
        return super().add_argument(*args, **kwargs)

    def add_to_parser(
            self, name, func, group, prefix="", exclude=[]):
        """Add function parameters to parser.

        Parameters
        ----------
        name : str
            Name of sub-object to create.
        func : callable
            Function to interpret; must have __doc__.
        group : str
            Argument group to create.
        exclude : str[]
            Arguments to exclude.
        prefix : str
            Prefix to prepend to argument name.

        Returns
        -------
        str[]
            List of arguments found in docstring.
        """
        parser = self.add_argument_group(group)

        doc = parse(func.__doc__, style=DocstringStyle.NUMPYDOC)
        sig = inspect.signature(func)
        self._group_names[name] = (
            prefix, [
                self._add_arg(parser, d, sig.parameters.get(d.arg_name))
                for d in doc.params if d.arg_name not in exclude
            ])

    def parse_args(self):
        """Parse arguments, grouping based on source objects."""
        parsed = {}
        args = super().parse_args()
        for name, (prefix, group_args) in self._group_names.items():
            parsed[name] = {
                arg.replace(prefix, ''): getattr(args, arg)
                for arg in group_args
            }
        for name in self._arg_names:
            parsed[name] = getattr(args, name)

        return parsed
