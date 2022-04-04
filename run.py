"""Run and test runtime."""

import numpy as np
from tqdm import tqdm
import threading
import time

from silverline import parse, parse_args, client


def _create_module(args, arts, rt, path):
    if args.type == 'PY':
        return arts.create_module_py(
            rt, name=path, aot=args.aot, path=path,
            argv=args.argv, env=args.env)
    else:
        return arts.create_module_wasm(
            rt, name=path, path=path, argv=args.argv, env=args.env)


def _get_runtime(rt_list, rt):
    try:
        return rt_list[rt]
    except KeyError:
        raise ValueError("Runtime not found: {}".format(rt))


def create_modules(args, arts, path):
    """Create modules with given executable path."""
    rt_list = arts.get_runtimes()
    return {
        rt: _create_module(args, arts, _get_runtime(rt_list, rt), path)
        for rt in args.runtime
    }


def _make_dp(args):
    return client.DirichletProcess(
        lambda: np.random.geometric(1 / args.mean_size), alpha=args.alpha)


def active_round(args, arts, modules):
    """Single round of active profiling."""
    profilers = [
        client.ActiveProfiler(
            _make_dp(args), arts, mod, n=args.n, delay=args.delay, pbar=i,
            desc=name, semaphore=threading.Semaphore())
        for i, (name, mod) in enumerate(modules.items())
    ]

    # Join on all "threads"; can't use thread.join() since MQTT is not
    # guaranteed to actually have real threads for each callback
    for p in profilers:
        p.semaphore.acquire()
    for p in profilers:
        p.pbar.close()


def timed_round(args, arts, modules):
    """Single round of timed profiling."""
    profilers = [
        client.TimedProfiler(
            _make_dp(args), arts, mod, delay=args.delay,
            semaphore=threading.Semaphore())
        for (_, mod) in modules.items()
    ]

    for _ in tqdm(range(100)):
        time.sleep(args.time / 100)

    for p in profilers:
        p.done = True
    for p in profilers:
        p.semaphore.acquire()


if __name__ == '__main__':

    args = parse_args(parse.http, parse.mqtt, parse.benchmark)
    arts = client.Client.from_args(args)

    tqdm.write("[Profiling] {} Runtimes: {}".format(
        len(args.runtime), " ".join(args.runtime)))

    if args.mode in {'active', 'timed'}:
        for i, path in enumerate(args.path):
            tqdm.write("[Profiling] {} Profiling Round {}/{}: {}".format(
                "Active" if args.mode == 'active' else "Timed",
                i + 1, len(args.path), path))
            modules = create_modules(args, arts, path)
            func = (active_round if args.mode == 'active' else timed_round)
            func(args, arts, modules)
    else:
        for path in args.path:
            create_modules(args, arts, path)

    arts.loop_stop()
