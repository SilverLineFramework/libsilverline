"""Benchmark Profilers."""

from tqdm import tqdm
import time
import threading

from .data import DirichletProcess


class ActiveProfiler:
    """Active fixed-iteration profiler.

    Parameters
    ----------
    data : callable
        Generator for random input data.
    client : paho.mqtt.client
        Mqtt client interface.
    module : str
        Module UUID to interact with.

    Keyword Args
    ------------
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
            self, data, client, module, n=100, delay=0.1, pbar=-1, desc='rt'):

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

    @classmethod
    def from_args(cls, args, client, module, pbar=-1, desc='rt'):
        """Construct from namespace such as ArgumentParser."""
        return cls(
            DirichletProcess.from_args(args), client, module, n=args.n,
            delay=args.delay, pbar=pbar, desc=desc)

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
    data : callable
        Generator for random input data.
    client : paho.mqtt.client
        Mqtt client interface.
    module : str
        Module UUID to interact with.

    Keyword Args
    ------------
    delay : float
        Delay in seconds between periods.
    """

    def __init__(self, data, client, module, delay=0.1):

        self.data = data
        self.client = client

        self.delay = delay
        self.topic = "benchmark/in/{}".format(module)
        self.semaphore = threading.Semaphore()
        self.semaphore.acquire()

        self.client.register_callback(
            "benchmark/out/{}".format(module), self.callback)

        self.done = False

    @classmethod
    def from_args(cls, args, client, module):
        """Construct from namespace such as ArgumentParser."""
        return cls(
            DirichletProcess.from_args(args), client, module, delay=args.delay)

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
            p.semaphore.acquire()


class PassiveProfiler:
    """Passive time-limited profiler.

    Parameters
    ----------
    client : paho.mqtt.client
        Mqtt client interface.
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
            p.semaphore.acquire()
