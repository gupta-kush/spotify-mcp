"""Shared helper functions."""


def chunked(lst: list, size: int):
    """Yield successive chunks of ``size`` from ``lst``."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def get_primary_artist(track: dict) -> str:
    """Get the primary artist name from a track dict."""
    artists = track.get("artists", [])
    if artists:
        return artists[0].get("name", "Unknown")
    return "Unknown"
