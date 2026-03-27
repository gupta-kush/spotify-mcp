"""Library management tools — 9 tools for saved/liked tracks and albums."""

import logging
from ..utils.spotify_client import get_client
from ..utils.errors import catch_spotify_errors
from ..utils.formatting import format_track_list, format_album_detail, format_episode
from ..utils.uri_parser import parse_spotify_id

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_saved_tracks(limit: int = 50, offset: int = 0) -> str:
        """Get your liked/saved tracks with pagination (limit up to 50, offset for paging)."""
        limit = max(1, min(50, limit))
        sp = get_client()
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = results.get("items", [])
        total = results.get("total", 0)

        header = f"**Liked Songs** (showing {offset + 1}–{offset + len(items)} of {total}):\n\n"
        # Extract the track from the saved-track wrapper
        tracks = [{"track": item.get("track")} for item in items]
        return header + format_track_list(tracks)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_save_tracks(uris: list[str]) -> str:
        """Save tracks to your Liked Songs (max 50 URIs per call)."""
        if not uris:
            return "**Error:** No track URIs provided."
        if len(uris) > 50:
            return "**Error:** Max 50 tracks per call."

        sp = get_client()
        # Extract track IDs from URIs
        track_ids = [parse_spotify_id(u) for u in uris]
        sp.current_user_saved_tracks_add(track_ids)
        return f"Saved {len(track_ids)} track(s) to your Liked Songs."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_remove_saved_tracks(uris: list[str], dry_run: bool = True) -> str:
        """Remove tracks from your Liked Songs (max 50 URIs per call).

        DESTRUCTIVE: Removes tracks from Liked Songs. Defaults to dry_run=True
        which only previews what would be removed. Set dry_run=False to execute.
        """
        if not uris:
            return "**Error:** No track URIs provided."
        if len(uris) > 50:
            return "**Error:** Max 50 tracks per call."

        if dry_run:
            return (
                f"**Dry run** — would remove {len(uris)} track(s) from Liked Songs.\n\n"
                f"URIs: {', '.join(uris[:10])}"
                f"{'...' if len(uris) > 10 else ''}\n\n"
                f"Set `dry_run=False` to execute."
            )

        sp = get_client()
        track_ids = [parse_spotify_id(u) for u in uris]
        sp.current_user_saved_tracks_delete(track_ids)
        return f"Removed {len(track_ids)} track(s) from your Liked Songs."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_saved_albums(limit: int = 20, offset: int = 0) -> str:
        """Get your saved albums with pagination (limit up to 50, offset for paging)."""
        limit = max(1, min(50, limit))
        sp = get_client()
        results = sp.current_user_saved_albums(limit=limit, offset=offset)
        items = results.get("items", [])
        total = results.get("total", 0)

        header = f"**Saved Albums** (showing {offset + 1}–{offset + len(items)} of {total}):\n\n"
        lines = [header]
        for i, item in enumerate(items, offset + 1):
            album = item.get("album")
            if album:
                lines.append(f"{i}. {format_album_detail(album)}")
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_save_albums(album_ids: list[str]) -> str:
        """Save albums to your library (max 50 per call)."""
        if not album_ids:
            return "**Error:** No album IDs provided."
        if len(album_ids) > 50:
            return "**Error:** Max 50 albums per call."
        sp = get_client()
        ids = [parse_spotify_id(a) for a in album_ids]
        sp.current_user_saved_albums_add(ids)
        return f"Saved {len(ids)} album(s) to your library."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_remove_saved_albums(album_ids: list[str], dry_run: bool = True) -> str:
        """Remove albums from your library (max 50 per call).

        DESTRUCTIVE: Removes albums from your library. Defaults to dry_run=True
        which only previews what would be removed. Set dry_run=False to execute.
        """
        if not album_ids:
            return "**Error:** No album IDs provided."
        if len(album_ids) > 50:
            return "**Error:** Max 50 albums per call."

        if dry_run:
            return (
                f"**Dry run** — would remove {len(album_ids)} album(s) from your library.\n\n"
                f"Set `dry_run=False` to execute."
            )

        sp = get_client()
        ids = [parse_spotify_id(a) for a in album_ids]
        sp.current_user_saved_albums_delete(ids)
        return f"Removed {len(ids)} album(s) from your library."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_check_saved_tracks(track_ids: list[str]) -> str:
        """Check which tracks are in your Liked Songs (max 50 per call)."""
        if not track_ids:
            return "**Error:** No track IDs provided."
        if len(track_ids) > 50:
            return "**Error:** Max 50 tracks per call."
        sp = get_client()
        ids = [parse_spotify_id(t) for t in track_ids]
        results = sp.current_user_saved_tracks_contains(ids)
        lines = ["**Saved Track Check:**", ""]
        for tid, saved in zip(ids, results):
            status = "Saved" if saved else "Not saved"
            lines.append(f"- `{tid}`: {status}")
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_check_saved_albums(album_ids: list[str]) -> str:
        """Check which albums are saved in your library (max 50 per call)."""
        if not album_ids:
            return "**Error:** No album IDs provided."
        if len(album_ids) > 50:
            return "**Error:** Max 50 albums per call."
        sp = get_client()
        ids = [parse_spotify_id(a) for a in album_ids]
        results = sp.current_user_saved_albums_contains(ids)
        lines = ["**Saved Album Check:**", ""]
        for aid, saved in zip(ids, results):
            status = "Saved" if saved else "Not saved"
            lines.append(f"- `{aid}`: {status}")
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_saved_episodes(limit: int = 20) -> str:
        """Get your saved podcast episodes (up to 50)."""
        limit = max(1, min(50, limit))
        sp = get_client()
        results = sp.current_user_saved_episodes(limit=limit)
        items = results.get("items", [])
        total = results.get("total", 0)

        if not items:
            return "You have no saved episodes."

        header = f"**Saved Episodes** ({total} total):\n\n"
        lines = [header]
        for i, item in enumerate(items, 1):
            episode = item.get("episode")
            if episode:
                lines.append(f"{i}. {format_episode(episode)}")
        return "\n".join(lines)
