"""Inspect function signature for parsing."""

import inspect
import argparse
import json
from docstring_parser import parse, DocstringStyle


class ArgumentParser(argparse.ArgumentParser):
    """Extension of ArgumentParser supporting addition through inspection."""

    def __init__(self, *args, **kwargs):

        self._group_names = {}
        self._arg_names = []
        self._defaults_func = {}
        super().__init__(*args, **kwargs)
        super().add_argument("--config", help=(
            "Config file to load; priority is (1) explicitly passed args, "
            "(2) config file, (3) defaults"))

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

    def set_default_func(self, **kwargs):
        """Set defaults (to be executed as function)."""
        self._defaults_func.update(kwargs)

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

    def parse_args(self, argv=[]):
        """Parse arguments, grouping based on source objects."""
        # Config
        args = super().parse_args(argv)
        if args.config:
            with open(args.config) as f:
                self.set_defaults(**json.load(f))

        # Func defaults
        args = super().parse_args()
        self.set_defaults(**{
            k: v(args) for k, v in self._defaults_func.items()
        })

        # Actual args
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
