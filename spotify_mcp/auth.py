import os
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth, CacheFileHandler
from .config import (
    SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI, SPOTIFY_CACHE_DIR, SCOPES,
)

logger = logging.getLogger(__name__)

_client = None


def get_spotify_client() -> spotipy.Spotify:
    """Get or create the singleton Spotipy client.

    On first call, triggers OAuth browser flow if no cached token exists.
    Subsequent calls return the same client instance (Spotipy handles token refresh).
    """
    global _client
    if _client is not None:
        return _client

    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set. "
            "See .env.example for details."
        )

    cache_path = os.path.join(SPOTIFY_CACHE_DIR, ".spotify_token_cache")
    handler = CacheFileHandler(cache_path=cache_path)

    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPES,
        cache_handler=handler,
        open_browser=True,
    )

    _client = spotipy.Spotify(auth_manager=auth_manager, retries=3, status_retries=3)
    logger.info("Spotify client initialized successfully")
    return _client
