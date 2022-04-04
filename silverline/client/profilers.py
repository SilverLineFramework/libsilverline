"""Benchmark Profilers."""

from tqdm import tqdm
import time


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
    semaphore : threading.Semaphore
        If not None, notifies after completion.
    """

    def __init__(
            self, data, client, module, n=100, delay=0.1, pbar=-1, desc='rt',
            semaphore=None):

        self.data = data
        self.client = client

        # `idx` counts the number of arrived packets, but the first packet
        # is really just an ACK packet sent after initialization!
        # The hack here is to start at an iteration deficit.
        self.idx = -1
        self.n = n
        self.delay = delay
        self.topic = "benchmark/in/{}".format(module)
        self.semaphore = semaphore

        self.client.register_callback(
            "benchmark/out/{}".format(module), self.callback)

        if pbar >= 0:
            self.pbar = tqdm(total=n, position=pbar, desc=desc)
        else:
            self.pbar = None

        if self.semaphore:
            self.semaphore.acquire()

    def callback(self, _):
        """Callback for triggering the next period."""
        if self.pbar and self.idx >= 0:
            self.pbar.update(1)
        self.idx += 1

        if self.idx >= self.n:
            self.client.publish(self.topic, b"exit")
            if self.semaphore:
                self.semaphore.release()
        else:
            time.sleep(self.delay)
            self.client.publish(self.topic, self.data.random_buffer())


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
    semaphore : threading.Semaphore
        If not None, notifies after completion.
    """

    def __init__(self, data, client, module, delay=0.1, semaphore=None):

        self.data = data
        self.client = client

        self.delay = delay
        self.topic = "benchmark/in/{}".format(module)
        self.semaphore = semaphore

        self.client.register_callback(
            "benchmark/out/{}".format(module), self.callback)

        self.done = False

    def callback(self, _):
        """Callback for triggering the next period."""
        if self.done:
            self.client.publish(self.topic, b"exit")
            if self.semaphore:
                self.semaphore.release()
        else:
            time.sleep(self.delay)
            self.client.publish(self.topic, self.data.random_buffer())
