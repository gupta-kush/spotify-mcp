"""Search tool — 1 versatile tool with auto-pagination."""

import logging
from ..utils.spotify_client import get_client
from ..utils.errors import catch_spotify_errors
from ..utils.pagination import search_with_pagination
from ..utils.formatting import format_track_list, format_artist_list, format_playlist_list, format_album

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    @catch_spotify_errors
    def spotify_search(
        query: str,
        type: str = "track",
        limit: int = 10,
    ) -> str:
        """Search Spotify for tracks, artists, albums, or playlists. Supports field filters like artist:, genre:, year: in the query."""
        limit = max(1, min(50, limit))
        sp = get_client()

        # Handle multi-type searches
        types = [t.strip() for t in type.split(",")]
        sections = []

        for search_type in types:
            if search_type not in ("track", "artist", "album", "playlist"):
                sections.append(f"**Error:** Unknown type '{search_type}'. Use track, artist, album, or playlist.")
                continue

            results = search_with_pagination(sp, query, search_type, limit)

            if not results:
                sections.append(f"**{search_type.title()}s:** No results found.")
                continue

            if search_type == "track":
                # Wrap in the format expected by format_track_list
                sections.append(f"**Tracks:**\n{format_track_list(results)}")
            elif search_type == "artist":
                sections.append(f"**Artists:**\n{format_artist_list(results)}")
            elif search_type == "album":
                lines = [f"**Albums:**"]
                for i, album in enumerate(results, 1):
                    lines.append(format_album(album, index=i))
                sections.append("\n".join(lines))
            elif search_type == "playlist":
                sections.append(f"**Playlists:**\n{format_playlist_list(results)}")

        return "\n\n".join(sections)
