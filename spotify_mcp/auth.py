import os
import logging
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyPKCE, CacheFileHandler
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

    Supports two auth modes:
    - **PKCE** (default): Only requires SPOTIFY_CLIENT_ID — no client secret needed.
    - **OAuth**: If SPOTIFY_CLIENT_SECRET is also set, uses the traditional OAuth flow.
    """
    global _client
    if _client is not None:
        return _client

    if not SPOTIFY_CLIENT_ID:
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID must be set.\n"
            "Options:\n"
            "  1. Run: spotify-mcp-setup\n"
            "  2. Set env vars in your Claude Desktop config\n"
            "  3. Copy .env.example to .env and fill in credentials\n"
            "See: https://developer.spotify.com/dashboard"
        )

    # Ensure cache directory exists
    cache_dir = Path(SPOTIFY_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_path = os.path.join(SPOTIFY_CACHE_DIR, ".spotify_token_cache")
    handler = CacheFileHandler(cache_path=cache_path)

    if SPOTIFY_CLIENT_SECRET:
        # Traditional OAuth flow (backward-compatible)
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SCOPES,
            cache_handler=handler,
            open_browser=True,
        )
        logger.info("Using OAuth flow (client secret provided)")
    else:
        # PKCE flow — no client secret needed
        auth_manager = SpotifyPKCE(
            client_id=SPOTIFY_CLIENT_ID,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SCOPES,
            cache_handler=handler,
            open_browser=True,
        )
        logger.info("Using PKCE flow (no client secret)")

    _client = spotipy.Spotify(auth_manager=auth_manager, retries=3, status_retries=3)
    logger.info("Spotify client initialized successfully")
    return _client
