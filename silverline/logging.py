"""Standardized loggging configuration."""

import logging


def configure_log(log=None, verbose=2):
    """Configure SilverLine logging.

    Uses the same convention as the linux runtime:
        0:ERROR -> 40
        1:NOTIF -> 30
        2:INFO -> 20
        3:DEBUG -> 10
        4:TRACE -> 5
        5:ALL -> 0

    Parameters
    ----------
    log : str
        File to save log to.
    verbose : int or str
        Logging level to use (0-5; 5 is most verbose).
    """
    level = {
        0: 40, 1: 30, 2: 20, 3: 10, 4: 5, 5: 0
    }.get(verbose, 0)

    logging.basicConfig(
        filename=log,
        level=level,
        format="[%(asctime)s] [%(module)s:%(levelname)s] %(message)s",
        datefmt="%H:%M:%S")
