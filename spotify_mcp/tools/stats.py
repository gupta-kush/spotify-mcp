"""Personalization and listening history tools — 3 tools."""

import logging
from ..utils.spotify_client import get_client
from ..utils.formatting import format_track_list, format_artist_list, format_track

logger = logging.getLogger(__name__)

VALID_TIME_RANGES = {
    "short_term": "last 4 weeks",
    "medium_term": "last 6 months",
    "long_term": "all time",
}


def register(mcp):

    @mcp.tool()
    def spotify_top_tracks(
        time_range: str = "medium_term",
        limit: int = 20,
    ) -> str:
        """Get your most-listened-to tracks.

        Args:
            time_range: Time period to analyze.
                        "short_term" = last 4 weeks,
                        "medium_term" = last 6 months (default),
                        "long_term" = all time.
            limit: Number of tracks to return (1-50). Default 20.
        """
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
    def spotify_top_artists(
        time_range: str = "medium_term",
        limit: int = 20,
    ) -> str:
        """Get your most-listened-to artists.

        Args:
            time_range: Time period to analyze.
                        "short_term" = last 4 weeks,
                        "medium_term" = last 6 months (default),
                        "long_term" = all time.
            limit: Number of artists to return (1-50). Default 20.
        """
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
    def spotify_recently_played(limit: int = 20) -> str:
        """Get your recently played tracks.

        Args:
            limit: Number of tracks to return (1-50). Default 20.

        Shows tracks in reverse chronological order with timestamps.
        """
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
