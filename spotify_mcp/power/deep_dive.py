"""Artist deep dive tool — comprehensive artist profile."""

import logging
from ..utils.spotify_client import get_client
from ..utils.pagination import fetch_artist_albums
from ..utils.formatting import format_album, format_artist_list

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    def spotify_artist_deep_dive(artist_id: str) -> str:
        """Get a comprehensive profile of an artist.

        Includes their genres, full discography overview, and related artists.
        Note: Artist top tracks and popularity are unavailable in the current
        Spotify API (removed Feb 2026).

        Args:
            artist_id: Spotify artist ID. Get this from search results.
        """
        sp = get_client()

        # Basic info
        artist = sp.artist(artist_id)
        name = artist.get("name", "Unknown")
        genres = artist.get("genres", [])
        images = artist.get("images", [])
        image_url = images[0]["url"] if images else None

        lines = [
            f"# {name}",
            "",
        ]

        if genres:
            lines.append(f"**Genres:** {', '.join(genres)}")
        if image_url:
            lines.append(f"**Image:** {image_url}")
        lines.append("")

        # Discography
        albums = fetch_artist_albums(sp, artist_id, include_groups="album,single,compilation")

        if albums:
            # Group by type
            albums_by_type = {}
            for album in albums:
                atype = album.get("album_type", "album")
                albums_by_type.setdefault(atype, []).append(album)

            lines.append(f"## Discography ({len(albums)} releases)")
            lines.append("")

            for atype in ["album", "single", "compilation"]:
                type_albums = albums_by_type.get(atype, [])
                if not type_albums:
                    continue

                label = atype.title() + ("s" if len(type_albums) != 1 else "")
                lines.append(f"### {label} ({len(type_albums)})")
                # Sort by release date (newest first)
                type_albums.sort(
                    key=lambda a: a.get("release_date", ""),
                    reverse=True,
                )
                for i, album in enumerate(type_albums[:20], 1):
                    lines.append(format_album(album, index=i))
                if len(type_albums) > 20:
                    lines.append(f"_...and {len(type_albums) - 20} more_")
                lines.append("")

        # Related artists
        related = sp.artist_related_artists(artist_id)
        related_artists = related.get("artists", [])

        if related_artists:
            lines.append(f"## Related Artists ({len(related_artists)})")
            lines.append("")
            lines.append(format_artist_list(related_artists[:15]))

        return "\n".join(lines)
