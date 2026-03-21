"""Shared error handling for Spotify API exceptions."""

import functools
import logging
from spotipy.exceptions import SpotifyException

logger = logging.getLogger(__name__)


def catch_spotify_errors(func):
    """Decorator that catches Spotify API errors and returns user-friendly messages."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SpotifyException as e:
            return handle_spotify_error(e)
        except ValueError as e:
            return f"**Error:** {e}"
    return wrapper


def handle_spotify_error(e: SpotifyException) -> str:
    """Convert a SpotifyException into a user-friendly error string.

    Returns a markdown-formatted error message suitable for tool output.
    """
    status = getattr(e, "http_status", None)
    msg = str(e)
    reason = getattr(e, "reason", "")

    # No active device
    if "NO_ACTIVE_DEVICE" in msg or "Player command failed: No active device" in msg:
        return (
            "**Error:** No active Spotify device found.\n\n"
            "Open Spotify on any device (phone, desktop, or web player) "
            "and start playing something, then try again."
        )

    # Premium required
    if status == 403 or "PREMIUM_REQUIRED" in msg or "premium" in msg.lower():
        return (
            "**Error:** This feature requires Spotify Premium.\n\n"
            "Upgrade at https://www.spotify.com/premium"
        )

    # Not found
    if status == 404:
        return (
            "**Error:** Resource not found. "
            "Check that the Spotify ID, URI, or URL is correct."
        )

    # Rate limited
    if status == 429:
        retry_after = ""
        if hasattr(e, "headers") and e.headers:
            seconds = e.headers.get("Retry-After", "")
            if seconds:
                retry_after = f" Try again in {seconds} seconds."
        return f"**Error:** Rate limited by Spotify.{retry_after}"

    # Auth expired
    if status == 401:
        return (
            "**Error:** Authorization expired or invalid.\n\n"
            "Delete `.spotify_token_cache` and restart to re-authorize."
        )

    # Generic fallback
    logger.error("Spotify API error (HTTP %s): %s", status, msg)
    if reason:
        return f"**Error:** Spotify API error: {reason}"
    return f"**Error:** Spotify API error: {msg}"
