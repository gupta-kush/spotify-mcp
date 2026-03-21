"""Playlist CRUD tools — 12 tools for playlist management."""

import logging
from ..utils.spotify_client import get_client
from ..utils.errors import catch_spotify_errors
from ..utils.formatting import (
    format_playlist_summary, format_playlist_list,
    format_track_list, ms_to_duration,
)
from ..utils.pagination import fetch_all_playlist_items
from ..utils.uri_parser import parse_spotify_id

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_my_playlists(limit: int = 50) -> str:
        """List your Spotify playlists.

        Args:
            limit: Max number of playlists to return (1-50). Default 50.

        Returns playlist names, track counts, and IDs.
        """
        limit = max(1, min(50, limit))
        sp = get_client()
        results = sp.current_user_playlists(limit=limit)
        playlists = results.get("items", [])
        total = results.get("total", 0)

        header = f"**Your Playlists** ({total} total):\n\n"
        return header + format_playlist_list(playlists)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_playlist(playlist_id: str) -> str:
        """Get details about a specific playlist including its tracks.

        Args:
            playlist_id: Spotify playlist ID or URI.

        Returns playlist metadata and the first batch of tracks.
        """
        sp = get_client()
        playlist = sp.playlist(playlist_id)

        lines = [format_playlist_summary(playlist), ""]

        # Show tracks
        tracks = playlist.get("tracks", {}).get("items", [])
        total = playlist.get("tracks", {}).get("total", 0)

        # Calculate total duration
        total_ms = sum(
            t.get("track", {}).get("duration_ms", 0)
            for t in tracks if t.get("track")
        )
        lines.append(f"**Duration:** {ms_to_duration(total_ms)} (first {len(tracks)} tracks)")
        lines.append("")
        lines.append(format_track_list(tracks))

        if total > len(tracks):
            lines.append(f"\n_Use `spotify_get_playlist_tracks` with offset to see more. {total} tracks total._")

        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_playlist_tracks(
        playlist_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> str:
        """Get tracks from a playlist with pagination support.

        Args:
            playlist_id: Spotify playlist ID or URI.
            limit: Number of tracks to return (1-100). Default 100.
            offset: Starting position (0-indexed). Default 0.

        Use offset to page through large playlists.
        """
        limit = max(1, min(100, limit))
        sp = get_client()
        results = sp.playlist_items(playlist_id, limit=limit, offset=offset)
        tracks = results.get("items", [])
        total = results.get("total", 0)

        header = f"**Tracks {offset + 1}–{offset + len(tracks)}** of {total}:\n\n"
        return header + format_track_list(tracks)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_create_playlist(
        name: str,
        description: str = "",
        public: bool = False,
    ) -> str:
        """Create a new empty playlist.

        Args:
            name: Name for the new playlist.
            description: Optional description.
            public: Whether the playlist should be public. Default False (private).

        Returns the new playlist's ID and URL.
        """
        sp = get_client()
        user_id = sp.me()["id"]
        playlist = sp.user_playlist_create(
            user=user_id,
            name=name,
            public=public,
            description=description,
        )
        pid = playlist["id"]
        url = playlist.get("external_urls", {}).get("spotify", "")
        return f"Created playlist **{name}**\nID: `{pid}`\nURL: {url}"

    @mcp.tool()
    @catch_spotify_errors
    def spotify_add_to_playlist(
        playlist_id: str,
        uris: list[str],
        position: int = None,
    ) -> str:
        """Add tracks to a playlist.

        Args:
            playlist_id: Spotify playlist ID.
            uris: List of Spotify track URIs (e.g., ["spotify:track:xxx", "spotify:track:yyy"]).
            position: Position to insert tracks (0-indexed). If omitted, appends to end.

        Tracks are added in the order provided. Max 100 per call.
        """
        if not uris:
            return "**Error:** No track URIs provided."
        if len(uris) > 100:
            return "**Error:** Max 100 tracks per call. Split into multiple calls."

        sp = get_client()
        kwargs = {"playlist_id": playlist_id, "items": uris}
        if position is not None:
            kwargs["position"] = position
        sp.playlist_add_items(**kwargs)
        return f"Added {len(uris)} track(s) to playlist `{playlist_id}`."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_remove_from_playlist(
        playlist_id: str,
        uris: list[str],
    ) -> str:
        """Remove tracks from a playlist.

        Args:
            playlist_id: Spotify playlist ID.
            uris: List of Spotify track URIs to remove.

        Removes ALL occurrences of each track from the playlist.
        """
        if not uris:
            return "**Error:** No track URIs provided."

        sp = get_client()
        # playlist_remove_all_occurrences_of_items expects list of URIs
        sp.playlist_remove_all_occurrences_of_items(playlist_id, uris)
        return f"Removed {len(uris)} track(s) from playlist `{playlist_id}`."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_reorder_playlist(
        playlist_id: str,
        range_start: int,
        insert_before: int,
        range_length: int = 1,
    ) -> str:
        """Move tracks within a playlist to a new position.

        Args:
            playlist_id: Spotify playlist ID.
            range_start: Position of the first track to move (0-indexed).
            insert_before: Position to insert the tracks before (0-indexed).
            range_length: Number of consecutive tracks to move. Default 1.

        Example: To move track at position 5 to position 0 (top):
        range_start=5, insert_before=0
        """
        sp = get_client()
        sp.playlist_reorder_items(
            playlist_id,
            range_start=range_start,
            insert_before=insert_before,
            range_length=range_length,
        )
        return (
            f"Moved {range_length} track(s) from position {range_start} "
            f"to before position {insert_before}."
        )

    @mcp.tool()
    @catch_spotify_errors
    def spotify_update_playlist(
        playlist_id: str,
        name: str = None,
        description: str = None,
        public: bool = None,
    ) -> str:
        """Update a playlist's name, description, or visibility.

        Args:
            playlist_id: Spotify playlist ID.
            name: New name (optional).
            description: New description (optional).
            public: Set to True for public, False for private (optional).
        """
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if public is not None:
            kwargs["public"] = public

        if not kwargs:
            return "**Error:** Provide at least one of: name, description, public."

        sp = get_client()
        sp.playlist_change_details(playlist_id, **kwargs)

        changes = []
        if name is not None:
            changes.append(f"name → '{name}'")
        if description is not None:
            changes.append(f"description updated")
        if public is not None:
            changes.append(f"{'public' if public else 'private'}")

        return f"Updated playlist `{playlist_id}`: {', '.join(changes)}"

    @mcp.tool()
    @catch_spotify_errors
    def spotify_follow_playlist(playlist_id: str) -> str:
        """Follow a playlist.

        Args:
            playlist_id: Spotify playlist ID or URI.
        """
        sp = get_client()
        sp.current_user_follow_playlist(playlist_id)
        return f"Now following playlist `{playlist_id}`."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_unfollow_playlist(playlist_id: str) -> str:
        """Unfollow a playlist.

        Args:
            playlist_id: Spotify playlist ID or URI.
        """
        sp = get_client()
        sp.current_user_unfollow_playlist(playlist_id)
        return f"Unfollowed playlist `{playlist_id}`."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_playlist_cover(playlist_id: str) -> str:
        """Get a playlist's cover image URL.

        Args:
            playlist_id: Spotify playlist ID or URI.
        """
        sp = get_client()
        playlist_id = parse_spotify_id(playlist_id)
        images = sp.playlist_cover_image(playlist_id)
        if not images:
            return "No cover image found for this playlist."
        lines = ["**Playlist Cover Images:**", ""]
        for img in images:
            w = img.get("width", "?")
            h = img.get("height", "?")
            url = img.get("url", "")
            lines.append(f"- {w}x{h}: {url}")
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_check_playlist_followers(playlist_id: str, user_ids: list[str]) -> str:
        """Check if specific users follow a playlist.

        Args:
            playlist_id: Spotify playlist ID or URI.
            user_ids: List of Spotify user IDs to check (max 5).
        """
        if not user_ids:
            return "**Error:** No user IDs provided."
        if len(user_ids) > 5:
            return "**Error:** Max 5 user IDs per call (Spotify API limit)."
        sp = get_client()
        playlist_id = parse_spotify_id(playlist_id)
        results = sp.playlist_is_following(playlist_id, user_ids)
        lines = ["**Playlist Follower Check:**", ""]
        for uid, following in zip(user_ids, results):
            status = "Following" if following else "Not following"
            lines.append(f"- `{uid}`: {status}")
        return "\n".join(lines)
