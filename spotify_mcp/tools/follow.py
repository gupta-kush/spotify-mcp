"""Follow management tools — 7 tools."""

import logging
from ..utils.spotify_client import get_client
from ..utils.errors import catch_spotify_errors
from ..utils.formatting import format_artist_list
from ..utils.pagination import fetch_followed_artists
from ..utils.uri_parser import parse_spotify_id

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    @catch_spotify_errors
    def spotify_follow_artists(artist_ids: list[str]) -> str:
        """Follow one or more artists.

        Args:
            artist_ids: List of Spotify artist IDs or URIs. Max 50 per call.
        """
        if not artist_ids:
            return "**Error:** No artist IDs provided."
        if len(artist_ids) > 50:
            return "**Error:** Max 50 artists per call."
        sp = get_client()
        ids = [parse_spotify_id(a) for a in artist_ids]
        sp.user_follow_artists(ids)
        return f"Now following {len(ids)} artist(s)."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_unfollow_artists(artist_ids: list[str]) -> str:
        """Unfollow one or more artists.

        Args:
            artist_ids: List of Spotify artist IDs or URIs. Max 50 per call.
        """
        if not artist_ids:
            return "**Error:** No artist IDs provided."
        if len(artist_ids) > 50:
            return "**Error:** Max 50 artists per call."
        sp = get_client()
        ids = [parse_spotify_id(a) for a in artist_ids]
        sp.user_unfollow_artists(ids)
        return f"Unfollowed {len(ids)} artist(s)."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_followed_artists(limit: int = 20) -> str:
        """Get your followed artists.

        Args:
            limit: Maximum number of artists to return (1-50). Default 20.
        """
        limit = max(1, min(50, limit))
        sp = get_client()
        artists = fetch_followed_artists(sp, limit)
        if not artists:
            return "You're not following any artists."
        header = f"**Followed Artists** ({len(artists)}):\n\n"
        return header + format_artist_list(artists)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_check_following_artists(artist_ids: list[str]) -> str:
        """Check if you follow specific artists.

        Args:
            artist_ids: List of Spotify artist IDs or URIs to check. Max 50 per call.
        """
        if not artist_ids:
            return "**Error:** No artist IDs provided."
        if len(artist_ids) > 50:
            return "**Error:** Max 50 artists per call."
        sp = get_client()
        ids = [parse_spotify_id(a) for a in artist_ids]
        results = sp.current_user_following_artists(ids)
        lines = ["**Following Check:**", ""]
        for aid, following in zip(ids, results):
            status = "Following" if following else "Not following"
            lines.append(f"- `{aid}`: {status}")
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_check_following_users(user_ids: list[str]) -> str:
        """Check if you follow specific Spotify users.

        Args:
            user_ids: List of Spotify user IDs to check.
        """
        if not user_ids:
            return "**Error:** No user IDs provided."
        sp = get_client()
        results = sp.current_user_following_users(user_ids)
        lines = ["**Following Check:**", ""]
        for uid, following in zip(user_ids, results):
            status = "Following" if following else "Not following"
            lines.append(f"- `{uid}`: {status}")
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_follow_users(user_ids: list[str]) -> str:
        """Follow one or more Spotify users.

        Args:
            user_ids: List of Spotify user IDs to follow.
        """
        if not user_ids:
            return "**Error:** No user IDs provided."
        sp = get_client()
        sp.user_follow_users(user_ids)
        return f"Now following {len(user_ids)} user(s)."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_unfollow_users(user_ids: list[str]) -> str:
        """Unfollow one or more Spotify users.

        Args:
            user_ids: List of Spotify user IDs to unfollow.
        """
        if not user_ids:
            return "**Error:** No user IDs provided."
        sp = get_client()
        sp.user_unfollow_users(user_ids)
        return f"Unfollowed {len(user_ids)} user(s)."
