"""Benchmark Profilers."""

from tqdm import tqdm
import time
import threading
import numpy as np

from .data import DirichletProcess


class ActiveProfiler:
    """Active fixed-iteration profiler.

    Parameters
    ----------
    client : Client
        SilverLine mqtt client interface.
    module : str
        Module UUID to interact with.
    data : DirichletProcess
        Generator for random input data.
    n : int
        Number of periods to run.
    delay : float
        Delay in seconds between periods.
    pbar : int
        If >=0, prints a progress bar at this position.
    desc : str
        Runtime name (displayed in progress bar).
    """

    def __init__(
            self, client, module, data, n=100, delay=0.1, pbar=-1, desc='rt'):

        self.data = data
        self.client = client

        # `idx` counts the number of arrived packets, but the first packet
        # is really just an ACK packet sent after initialization!
        # The hack here is to start at an iteration deficit.
        self.idx = -1
        self.n = n
        self.delay = delay
        self.topic = "benchmark/in/{}".format(module)
        self.semaphore = threading.Semaphore()
        self.semaphore.acquire()

        self.client.register_callback(
            "benchmark/out/{}".format(module), self.callback)

        if pbar >= 0:
            self.pbar = tqdm(total=n, position=pbar, desc=desc)
        else:
            self.pbar = None

    def callback(self, _):
        """Callback for triggering the next period."""
        if self.pbar and self.idx >= 0:
            self.pbar.update(1)
        self.idx += 1

        if self.idx >= self.n:
            self.client.publish(self.topic, b"exit")
            self.semaphore.release()
        else:
            time.sleep(self.delay)
            self.client.publish(self.topic, self.data.generate())

    @staticmethod
    def run(profilers):
        """Run profilers and join on completion."""
        # Join on all "threads"; can't use thread.join() since MQTT is not
        # guaranteed to actually have real threads for each callback
        for p in profilers:
            p.semaphore.acquire()
        for p in profilers:
            if p.pbar is not None:
                p.pbar.close()


class TimedProfiler:
    """Active time-limited profiler.

    Parameters
    ----------
    client : Client
        SilverLine mqtt client interface.
    module : str
        Module UUID to interact with.
    data : DirichletProcess
        Generator for random input data.
    delay : float
        Delay in seconds between periods.
    """

    def __init__(self, client, module, data, delay=0.1):

        self.data = data
        self.client = client

        self.delay = delay
        self.topic = "benchmark/in/{}".format(module)
        self.semaphore = threading.Semaphore()
        self.semaphore.acquire()

        self.client.register_callback(
            "benchmark/out/{}".format(module), self.callback)

        self.done = False

    def callback(self, _):
        """Callback for triggering the next period."""
        if self.done:
            self.client.publish(self.topic, b"exit")
            self.semaphore.release()
        else:
            time.sleep(self.delay)
            self.client.publish(self.topic, self.data.generate())

    @staticmethod
    def run(profilers, duration=60):
        """Run profilers and terminate after timeout."""
        for _ in tqdm(range(100)):
            time.sleep(duration / 100)

        for p in profilers:
            p.done = True
        for p in profilers:
            p.semaphore.acquire(timeout=10)


class PassiveProfiler:
    """Passive time-limited profiler.

    Parameters
    ----------
    client : Client
        SilverLine mqtt client interface.
    module : str
        Module UUID to interact with.
    """

    def __init__(self, client, module):

        self.client = client
        self.topic = "benchmark/in/{}".format(module)

        self.semaphore = threading.Semaphore()
        self.semaphore.acquire()

        self.client.register_callback(
            "benchmark/out/{}".format(module), self.callback)

    def callback(self, _):
        """Callback to ensure the last iteration finishes."""
        self.semaphore.release()

    @staticmethod
    def run(profilers, duration=60):
        """Terminate modules after timeout."""
        for _ in tqdm(range(100)):
            time.sleep(duration / 100)

        for p in profilers:
            p.client.publish(p.topic, b"exit")
        for p in profilers:
            p.semaphore.acquire(timeout=10)


def run_profilers(
        client, modules,
        type="run", mean_size=1000., alpha=1., n=100, delay=0.1, duration=60.):
    """Create and run profilers.

    Parameters
    ----------
    client : Client
        SilverLine client interface.
    modules : dict
        Dictionary containing module names (key) and IDs (value) to profile.
    type : str
        Profiler type. Can be: `run` (just run, do nothing), `active`
        (active profiling with fixed rounds), `timed` (active profiling with
        time limit), and `passive` (spawn and wait)
    n : int
        Number of rounds for `active` profiler.
    delay : float
        Delay between rounds for `active` and `timed` profilers.
    mean_size : float
        Samples each data packet from Geometric(1 / mean_size) for `active` and
        `timed` profilers.
    alpha : float
        Dirichlet process new table probability for `active` and `timed`.
    duration : float
        Profiling duration for `timed` and `passive` profilers.
    """
    def _make_dp():
        return DirichletProcess(
            lambda: np.random.geometric(1 / mean_size), alpha=alpha)

    if type == "active":
        profilers = [
            ActiveProfiler(
                client, mod, _make_dp(), delay=delay, n=n, pbar=i, desc=rt)
            for i, ((rt, _), mod) in enumerate(modules.items())]
        ActiveProfiler.run(profilers)
    elif type == "timed":
        profilers = [
            TimedProfiler(client, mod, _make_dp(), delay=delay)
            for (_, mod) in modules.items()]
        TimedProfiler.run(profilers, duration=duration)
    elif type == "passive":
        profilers = [
            PassiveProfiler(client, mod)
            for (_, mod) in modules.items()]
        PassiveProfiler.run(profilers, duration=duration)
    elif type == "run":
        pass
    else:
        raise ValueError("Invalid profiling mode: {}".format(type))
