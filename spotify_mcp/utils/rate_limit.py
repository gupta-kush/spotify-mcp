"""Rate limit handling for Spotify API calls."""

import time
import logging
import functools
from spotipy.exceptions import SpotifyException

logger = logging.getLogger(__name__)


def retry_on_rate_limit(max_retries: int = 3):
    """Decorator that retries on 429 (rate limit) with exponential backoff.

    Spotipy has built-in retry for 429s, but this provides an additional
    safety net for cases where Spotipy's retries are exhausted.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except SpotifyException as e:
                    if e.http_status == 429 and attempt < max_retries:
                        retry_after = int(e.headers.get("Retry-After", 1)) if e.headers else 1
                        wait_time = max(retry_after, 2 ** attempt)
                        logger.warning(
                            f"Rate limited. Retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                    else:
                        raise
        return wrapper
    return decorator


def throttled_batch(func, items, delay: float = 0.1):
    """Call a function for each item with a small delay between calls.

    Useful for sequential individual API calls (e.g., fetching artist data
    one at a time since batch endpoints were removed in Feb 2026).

    Args:
        func: Function to call for each item.
        items: Iterable of items to process.
        delay: Seconds to wait between calls.

    Returns:
        List of results.
    """
    results = []
    for i, item in enumerate(items):
        if i > 0:
            time.sleep(delay)
        results.append(func(item))
    return results
