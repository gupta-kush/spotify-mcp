"""Browse tools — 4 tools for looking up tracks, albums, artists, and users."""

import logging
from ..utils.spotify_client import get_client
from ..utils.formatting import format_track, format_album_detail, format_artist, ms_to_duration

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    def spotify_get_track(track_id: str) -> str:
        """Get detailed information about a track.

        Args:
            track_id: Spotify track ID or URI.
        """
        sp = get_client()
        track_id = track_id.split(":")[-1] if ":" in track_id else track_id
        track = sp.track(track_id)

        artists = ", ".join(a["name"] for a in track.get("artists", []))
        album = track.get("album", {})
        duration = track.get("duration_ms", 0)

        lines = [
            f"# {track.get('name', 'Unknown')}",
            "",
            f"**Artist(s):** {artists}",
            f"**Album:** {album.get('name', 'Unknown')} ({album.get('release_date', '?')})",
            f"**Duration:** {ms_to_duration(duration)}",
            f"**Popularity:** {track.get('popularity', '?')}/100",
            f"**Explicit:** {'Yes' if track.get('explicit') else 'No'}",
            f"**Track Number:** {track.get('track_number', '?')} of {album.get('total_tracks', '?')}",
            f"**Disc:** {track.get('disc_number', 1)}",
            "",
            f"ID: `{track.get('id', '')}`",
            f"URI: `{track.get('uri', '')}`",
        ]
        url = track.get("external_urls", {}).get("spotify", "")
        if url:
            lines.append(f"URL: {url}")
        preview = track.get("preview_url")
        if preview:
            lines.append(f"Preview: {preview}")
        isrc = track.get("external_ids", {}).get("isrc")
        if isrc:
            lines.append(f"ISRC: `{isrc}`")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_get_album(album_id: str) -> str:
        """Get detailed information about an album including its tracklist.

        Args:
            album_id: Spotify album ID or URI.
        """
        sp = get_client()
        album_id = album_id.split(":")[-1] if ":" in album_id else album_id
        album = sp.album(album_id)

        artists = ", ".join(a["name"] for a in album.get("artists", []))
        tracks = album.get("tracks", {}).get("items", [])
        total_ms = sum(t.get("duration_ms", 0) for t in tracks)

        lines = [
            f"# {album.get('name', 'Unknown')}",
            "",
            f"**Artist(s):** {artists}",
            f"**Release Date:** {album.get('release_date', '?')}",
            f"**Type:** {album.get('album_type', 'album').title()}",
            f"**Tracks:** {album.get('total_tracks', '?')}",
            f"**Duration:** {ms_to_duration(total_ms)}",
            f"**Label:** {album.get('label', '?')}",
            f"**Popularity:** {album.get('popularity', '?')}/100",
            "",
        ]

        # Genres (if any)
        genres = album.get("genres", [])
        if genres:
            lines.append(f"**Genres:** {', '.join(genres)}")
            lines.append("")

        # Copyrights
        copyrights = album.get("copyrights", [])
        if copyrights:
            lines.append(f"**Copyright:** {copyrights[0].get('text', '')}")
            lines.append("")

        # Tracklist
        lines.append("## Tracklist")
        lines.append("")
        for t in tracks:
            dur = t.get("duration_ms", 0)
            minutes = dur // 60000
            seconds = (dur % 60000) // 1000
            lines.append(f"{t.get('track_number', '?')}. **{t.get('name', '?')}** [{minutes}:{seconds:02d}]")

        lines.append("")
        lines.append(f"ID: `{album.get('id', '')}`")
        url = album.get("external_urls", {}).get("spotify", "")
        if url:
            lines.append(f"URL: {url}")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_get_artist(artist_id: str) -> str:
        """Get detailed information about an artist.

        Args:
            artist_id: Spotify artist ID or URI.
        """
        sp = get_client()
        artist_id = artist_id.split(":")[-1] if ":" in artist_id else artist_id
        artist = sp.artist(artist_id)

        lines = [
            f"# {artist.get('name', 'Unknown')}",
            "",
            f"**Followers:** {artist.get('followers', {}).get('total', 0):,}",
            f"**Popularity:** {artist.get('popularity', '?')}/100",
        ]

        genres = artist.get("genres", [])
        if genres:
            lines.append(f"**Genres:** {', '.join(genres)}")

        images = artist.get("images", [])
        if images:
            lines.append(f"**Image:** {images[0].get('url', '')}")

        lines.append("")
        lines.append(f"ID: `{artist.get('id', '')}`")
        url = artist.get("external_urls", {}).get("spotify", "")
        if url:
            lines.append(f"URL: {url}")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_get_user(user_id: str) -> str:
        """Get a Spotify user's public profile.

        Args:
            user_id: Spotify user ID.
        """
        sp = get_client()
        user = sp.user(user_id)

        lines = [
            f"# {user.get('display_name', user.get('id', 'Unknown'))}",
            "",
            f"**User ID:** `{user.get('id', '')}`",
            f"**Followers:** {user.get('followers', {}).get('total', 0):,}",
        ]

        images = user.get("images", [])
        if images:
            lines.append(f"**Image:** {images[0].get('url', '')}")

        url = user.get("external_urls", {}).get("spotify", "")
        if url:
            lines.append(f"**Profile:** {url}")

        # Also fetch their public playlists
        playlists = sp.user_playlists(user.get("id", ""), limit=10)
        items = playlists.get("items", [])
        total = playlists.get("total", 0)
        if items:
            lines.append("")
            lines.append(f"## Public Playlists ({total} total)")
            lines.append("")
            for i, p in enumerate(items, 1):
                name = p.get("name", "Unknown")
                tracks = p.get("tracks", {}).get("total", 0)
                lines.append(f"{i}. **{name}** — {tracks} tracks | ID: `{p.get('id', '')}`")

        return "\n".join(lines)
