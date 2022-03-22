"""Python Module."""

import time


class Module:
    """Python Module."""


class Profile:
    """Profile data."""

    def __init__(self):
        self.process = psutil.Proces(os.getpid())
        self.reset()

    def commit(self):
        """Commit profile data."""
        self.end = time.perf_counter()
        self.memory = self.process.memory_info().rss

    def reset(self):
        """Reset profile data."""
        self.start = time.perf_counter()
        self.ch_in = 0
        self.ch_out = 0

    def encode(self):
        """Encode data body."""
        return {
            "start_time": int(self.start * 10**9),
            "end_time": int(self.end * 10**9),
            "runtime": int((self.end - self.start) * 10**9),
            "memory": self.memory,
            "ch_in": self.ch_in,
            "ch_out": self.ch_out
        }
