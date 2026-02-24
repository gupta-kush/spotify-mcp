import logging
import spotipy
from ..auth import get_spotify_client

logger = logging.getLogger(__name__)

# In-memory artist cache to avoid re-fetching the same artist
# (batch /artists endpoint is gone as of Feb 2026)
_artist_cache: dict = {}


def get_client() -> spotipy.Spotify:
    """Get the shared Spotipy client instance."""
    return get_spotify_client()


def get_artist_cached(sp: spotipy.Spotify, artist_id: str) -> dict:
    """Fetch artist data with session-level caching.

    Since batch GET /artists is gone, power tools that need data for many
    artists would otherwise make hundreds of individual API calls.
    This cache prevents re-fetching the same artist within a session.
    """
    if artist_id in _artist_cache:
        return _artist_cache[artist_id]

    artist = sp.artist(artist_id)
    _artist_cache[artist_id] = artist
    return artist


def clear_artist_cache():
    """Clear the artist cache (useful for testing)."""
    _artist_cache.clear()
