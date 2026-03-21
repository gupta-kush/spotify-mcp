"""Playlist sorting tool — 1 tool."""

import logging
from ..utils.spotify_client import get_client
from ..utils.pagination import fetch_all_playlist_items
from ..utils.formatting import ms_to_duration
from ..utils.helpers import chunked

logger = logging.getLogger(__name__)

SORT_OPTIONS = {
    "track_name": "Sort by track name (A-Z)",
    "artist_name": "Sort by primary artist name (A-Z)",
    "album_name": "Sort by album name (A-Z)",
    "duration": "Sort by track duration",
    "date_added": "Sort by date added to playlist",
}


def register(mcp):

    @mcp.tool()
    def spotify_sort_playlist(
        playlist_id: str,
        sort_by: str = "artist_name",
        reverse: bool = False,
    ) -> str:
        """Sort a playlist by track_name, artist_name, album_name, duration, or date_added."""
        if sort_by not in SORT_OPTIONS:
            available = "\n".join(f"- **{k}**: {v}" for k, v in SORT_OPTIONS.items())
            return f"**Error:** Unknown sort option '{sort_by}'. Available:\n{available}"

        sp = get_client()
        playlist_info = sp.playlist(playlist_id, fields="name")
        playlist_name = playlist_info.get("name", "Unknown")

        items = fetch_all_playlist_items(sp, playlist_id)
        if len(items) < 2:
            return f"Playlist '{playlist_name}' has fewer than 2 tracks — nothing to sort."

        # Build sortable list with metadata
        sortable = []
        for item in items:
            track = item.get("track")
            if not track or not track.get("uri"):
                continue
            sortable.append({
                "track": track,
                "uri": track["uri"],
                "track_name": track.get("name", "").lower(),
                "artist_name": track.get("artists", [{}])[0].get("name", "").lower(),
                "album_name": track.get("album", {}).get("name", "").lower(),
                "duration": track.get("duration_ms", 0),
                "date_added": item.get("added_at", ""),
            })

        # Sort
        sortable.sort(key=lambda x: x[sort_by], reverse=reverse)

        # Replace playlist contents
        sorted_uris = [s["uri"] for s in sortable]
        sp.playlist_replace_items(playlist_id, [])  # Clear
        for batch in chunked(sorted_uris, 100):
            sp.playlist_add_items(playlist_id, batch)

        direction = "descending" if reverse else "ascending"
        return (
            f"**Sorted** \"{playlist_name}\" by **{sort_by}** ({direction}).\n"
            f"Reordered {len(sortable)} tracks."
        )
