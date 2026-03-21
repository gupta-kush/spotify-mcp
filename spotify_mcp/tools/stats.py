"""Personalization and listening history tools — 3 tools."""

import logging
from ..utils.spotify_client import get_client
from ..utils.errors import catch_spotify_errors
from ..utils.formatting import format_track_list, format_artist_list, format_track

logger = logging.getLogger(__name__)

VALID_TIME_RANGES = {
    "short_term": "last 4 weeks",
    "medium_term": "last 6 months",
    "long_term": "all time",
}


def register(mcp):

    @mcp.tool()
    @catch_spotify_errors
    def spotify_top_tracks(
        time_range: str = "medium_term",
        limit: int = 20,
    ) -> str:
        """Get your top tracks by time range (short_term/medium_term/long_term), up to 50."""
        if time_range not in VALID_TIME_RANGES:
            return f"**Error:** time_range must be one of: {', '.join(VALID_TIME_RANGES.keys())}"
        limit = max(1, min(50, limit))

        sp = get_client()
        results = sp.current_user_top_tracks(time_range=time_range, limit=limit)
        tracks = results.get("items", [])

        period = VALID_TIME_RANGES[time_range]
        header = f"**Your Top Tracks** ({period}):\n\n"
        return header + format_track_list(tracks)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_top_artists(
        time_range: str = "medium_term",
        limit: int = 20,
    ) -> str:
        """Get your top artists by time range (short_term/medium_term/long_term), up to 50."""
        if time_range not in VALID_TIME_RANGES:
            return f"**Error:** time_range must be one of: {', '.join(VALID_TIME_RANGES.keys())}"
        limit = max(1, min(50, limit))

        sp = get_client()
        results = sp.current_user_top_artists(time_range=time_range, limit=limit)
        artists = results.get("items", [])

        period = VALID_TIME_RANGES[time_range]
        header = f"**Your Top Artists** ({period}):\n\n"
        return header + format_artist_list(artists)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_recently_played(limit: int = 20) -> str:
        """Get your recently played tracks in reverse chronological order, up to 50."""
        limit = max(1, min(50, limit))
        sp = get_client()
        results = sp.current_user_recently_played(limit=limit)
        items = results.get("items", [])

        if not items:
            return "No recently played tracks found."

        lines = [f"**Recently Played** ({len(items)} tracks):\n"]
        for i, item in enumerate(items, 1):
            track = item.get("track", {})
            played_at = item.get("played_at", "")
            # Format: "2024-01-15T12:30:00.000Z" -> "2024-01-15 12:30"
            timestamp = played_at[:16].replace("T", " ") if played_at else ""
            track_line = format_track(track, index=i)
            lines.append(f"{track_line} — _{timestamp}_")

        return "\n".join(lines)
