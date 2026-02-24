"""Shared helper functions."""


def chunked(lst: list, size: int):
    """Yield successive chunks of ``size`` from ``lst``."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]
