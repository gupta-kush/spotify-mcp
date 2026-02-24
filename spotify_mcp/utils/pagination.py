"""Pagination helpers for Spotify API endpoints."""

import logging
import time
from ..config import MAX_SEARCH_PAGE, MAX_PLAYLIST_PAGE

logger = logging.getLogger(__name__)


def fetch_all_playlist_items(sp, playlist_id: str, fields: str = None) -> list:
    """Fetch ALL items from a playlist, handling pagination.

    Args:
        sp: Spotipy client instance.
        playlist_id: Spotify playlist ID.
        fields: Optional fields filter to reduce response size.

    Returns:
        List of playlist item dicts.
    """
    items = []
    offset = 0
    while True:
        kwargs = {
            "playlist_id": playlist_id,
            "limit": MAX_PLAYLIST_PAGE,
            "offset": offset,
        }
        if fields:
            kwargs["fields"] = fields
        page = sp.playlist_items(**kwargs)
        page_items = page.get("items", [])
        items.extend(page_items)
        if page.get("next") is None or not page_items:
            break
        offset += MAX_PLAYLIST_PAGE
    return items


def search_with_pagination(sp, query: str, search_type: str, total_desired: int = 20) -> list:
    """Search with automatic pagination (max 10 per page as of Feb 2026).

    Args:
        sp: Spotipy client instance.
        query: Search query string.
        search_type: One of "track", "artist", "album", "playlist".
        total_desired: Total results to collect.

    Returns:
        List of result items.
    """
    results = []
    offset = 0
    key = f"{search_type}s"  # "track" -> "tracks"

    while len(results) < total_desired:
        page = sp.search(
            q=query,
            type=search_type,
            limit=MAX_SEARCH_PAGE,
            offset=offset,
        )
        page_items = page.get(key, {}).get("items", [])
        if not page_items:
            break
        results.extend(page_items)
        if page.get(key, {}).get("next") is None:
            break
        offset += MAX_SEARCH_PAGE

    return results[:total_desired]


def fetch_all_saved_tracks(sp, limit: int = None) -> list:
    """Fetch user's saved/liked tracks with pagination.

    Args:
        sp: Spotipy client instance.
        limit: Max tracks to fetch. None = fetch all.

    Returns:
        List of saved track item dicts.
    """
    items = []
    offset = 0
    page_size = 50  # saved tracks endpoint allows up to 50

    while True:
        page = sp.current_user_saved_tracks(limit=page_size, offset=offset)
        page_items = page.get("items", [])
        items.extend(page_items)
        if page.get("next") is None or not page_items:
            break
        if limit and len(items) >= limit:
            break
        offset += page_size

    if limit:
        return items[:limit]
    return items


def fetch_artist_albums(sp, artist_id: str, include_groups: str = "album,single") -> list:
    """Fetch all albums for an artist with pagination.

    Args:
        sp: Spotipy client instance.
        artist_id: Spotify artist ID.
        include_groups: Comma-separated album types (album, single, compilation, appears_on).

    Returns:
        List of album dicts.
    """
    albums = []
    offset = 0
    while True:
        page = sp.artist_albums(
            artist_id,
            include_groups=include_groups,
            limit=50,
            offset=offset,
        )
        page_items = page.get("items", [])
        albums.extend(page_items)
        if page.get("next") is None or not page_items:
            break
        offset += 50
    return albums


def fetch_all_saved_albums(sp, limit: int = None) -> list:
    """Fetch user's saved albums with pagination.

    Args:
        sp: Spotipy client instance.
        limit: Max albums to fetch. None = fetch all.

    Returns:
        List of saved album item dicts.
    """
    items = []
    offset = 0
    page_size = 20  # saved albums endpoint allows up to 20

    while True:
        page = sp.current_user_saved_albums(limit=page_size, offset=offset)
        page_items = page.get("items", [])
        items.extend(page_items)
        if page.get("next") is None or not page_items:
            break
        if limit and len(items) >= limit:
            break
        offset += page_size

    if limit:
        return items[:limit]
    return items


def fetch_followed_artists(sp, limit: int = 50) -> list:
    """Fetch user's followed artists with cursor-based pagination.

    Args:
        sp: Spotipy client instance.
        limit: Max artists to fetch. Clamped to 50 per page.

    Returns:
        List of artist dicts.
    """
    artists = []
    page_size = max(1, min(50, limit))
    cursor = None

    while True:
        result = sp.current_user_followed_artists(limit=page_size, after=cursor)
        page_items = result.get("artists", {}).get("items", [])
        artists.extend(page_items)
        if not page_items:
            break
        cursor = result.get("artists", {}).get("cursors", {}).get("after")
        if cursor is None:
            break

    return artists