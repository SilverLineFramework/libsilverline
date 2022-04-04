"""Run and test runtime."""

from tqdm import tqdm
from silverline import parse, parse_args
from silverline.client import (
    Client, TimedProfiler, ActiveProfiler, PassiveProfiler)


def _get_runtime(rt_list, rt):
    try:
        return rt_list[rt]
    except KeyError:
        raise ValueError("Runtime not found: {}".format(rt))


def create_modules(args, arts, path):
    """Create modules with given executable path."""
    rt_list = arts.get_runtimes()
    return {
        rt: arts.create_module_args(args, _get_runtime(rt_list, rt), path)
        for rt in args.runtime
    }


class Modes:
    """Namespace for execution modes."""

    @staticmethod
    def active(args, arts, modules):
        """Single round of active profiling."""
        profilers = [
            ActiveProfiler.from_args(args, arts, mod, pbar=i, desc=name)
            for i, (name, mod) in enumerate(modules.items())]
        ActiveProfiler.run(profilers)

    @staticmethod
    def timed(args, arts, modules):
        """Single round of timed profiling."""
        profilers = [
            TimedProfiler.from_args(args, arts, mod)
            for (_, mod) in modules.items()]
        TimedProfiler.run(profilers, duration=args.time)

    @staticmethod
    def passive(args, arts, modules):
        """Single round of timed passive profiling."""
        profilers = [
            PassiveProfiler(arts, mod)
            for (_, mod) in modules.items()]
        PassiveProfiler.run(profilers, duration=args.time)

    @staticmethod
    def run(args, arts, modules):
        """Launch modules only."""
        pass


def _main():
    arts = Client.from_args(args)

    tqdm.write("[Profiling] {} Runtimes: {}".format(
        len(args.runtime), " ".join(args.runtime)))

    for i, path in enumerate(args.path):
        if args.mode != 'run':
            tqdm.write("[Profiling] {} Profiling Round {}/{}: {}".format(
                args.mode.capitalize(), i + 1, len(args.path), path))
        modules = create_modules(args, arts, path)
        getattr(Modes, args.mode)(args, arts, modules)

    arts.loop_stop()


if __name__ == '__main__':
    args = parse_args(parse.http, parse.mqtt, parse.benchmark)
    _main(args)
