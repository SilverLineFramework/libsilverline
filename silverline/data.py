"""Benchmark data generation schemes."""

import os
import numpy as np


class DirichletProcess:
    """Dirichlet Process.

    Parameters
    ----------
    prior
        Distribution for each dirichlet process cluster.
    alpha : float
        Dirichlet process new table probability.
    """

    def __init__(self, prior, alpha=1.):
        self.tables = []
        self.values = []

        self.prior = prior
        self.alpha = alpha

    def draw(self):
        """Sample from DP and update hidden state."""
        weights = [self.alpha] + self.tables
        weights = np.array(weights) / np.sum(weights)
        idx = np.random.choice(len(weights), 1, p=weights)[0]
        if idx == 0:
            self.tables.append(1)
            self.values.append(self.prior())
            return self.values[-1]
        else:
            self.tables[idx - 1] += 1
            return self.values[idx - 1]

    def generate(self, min_size=4):
        """Generate random buffer with size drawn from this DP."""
        size = self.draw() + min_size
        return b">>> " + os.urandom(size - 4)
