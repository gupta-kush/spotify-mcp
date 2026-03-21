"""Music discovery tools — 5 tools using available API primitives.

Since Spotify deprecated the recommendations API (Feb 2026), discovery
is built from: search, related artists, and artist albums.
"""

import logging
import random
from ..utils.spotify_client import get_client
from ..utils.errors import catch_spotify_errors
from ..utils.pagination import search_with_pagination, fetch_artist_albums
from ..utils.formatting import format_track_list, format_artist_list, format_track
from ..config import MOOD_GENRE_MAP

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    @catch_spotify_errors
    def spotify_related_artists(artist_id: str) -> str:
        """Get up to 20 artists similar to a given artist."""
        sp = get_client()
        result = sp.artist_related_artists(artist_id)
        related = result.get("artists", [])

        if not related:
            return "No related artists found."

        # Get the source artist name for context
        source = sp.artist(artist_id)
        source_name = source.get("name", "this artist")

        header = f"**Artists related to {source_name}:**\n\n"
        return header + format_artist_list(related)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_discover_by_artist(artist_id: str, limit: int = 20) -> str:
        """Discover tracks from an artist's related artists' recent albums (1-50)."""
        limit = max(1, min(50, limit))
        sp = get_client()

        # Get the source artist for context
        source = sp.artist(artist_id)
        source_name = source.get("name", "this artist")

        # Get related artists
        result = sp.artist_related_artists(artist_id)
        related = result.get("artists", [])

        if not related:
            return f"No related artists found for {source_name}."

        # Collect tracks from related artists' albums
        all_tracks = []
        # Sample a subset of related artists to avoid too many API calls
        sample_artists = related[:8]

        for artist in sample_artists:
            albums = fetch_artist_albums(sp, artist["id"], include_groups="album,single")
            if not albums:
                continue
            # Pick the most recent album
            recent_album = albums[0]
            album_tracks = sp.album_tracks(recent_album["id"], limit=5)
            for track in album_tracks.get("items", []):
                # Add artist/album context since album_tracks doesn't include full info
                track["artists"] = track.get("artists", recent_album.get("artists", []))
                track["album"] = {"name": recent_album.get("name", "")}
                all_tracks.append(track)

            if len(all_tracks) >= limit * 2:
                break

        if not all_tracks:
            return f"Could not find tracks from artists related to {source_name}."

        # Shuffle and pick
        random.shuffle(all_tracks)
        selected = all_tracks[:limit]

        header = f"**Tracks discovered via artists related to {source_name}:**\n\n"
        return header + format_track_list(selected)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_discover_by_mood(mood: str, limit: int = 20) -> str:
        """Discover tracks by mood (happy, sad, energetic, chill, focused, romantic, angry, party)."""
        mood_lower = mood.lower().strip()
        if mood_lower not in MOOD_GENRE_MAP:
            available = ", ".join(sorted(MOOD_GENRE_MAP.keys()))
            return f"**Error:** Unknown mood '{mood}'. Supported moods: {available}"

        limit = max(1, min(50, limit))
        genres = MOOD_GENRE_MAP[mood_lower]
        sp = get_client()

        # Search across the mood's associated genres
        all_tracks = []
        tracks_per_genre = max(3, limit // len(genres))

        for genre in genres:
            query = f"genre:{genre}"
            results = search_with_pagination(sp, query, "track", tracks_per_genre)
            all_tracks.extend(results)

            if len(all_tracks) >= limit * 2:
                break

        if not all_tracks:
            return f"No tracks found for mood '{mood}'."

        # Deduplicate by track ID and shuffle
        seen_ids = set()
        unique_tracks = []
        for t in all_tracks:
            tid = t.get("id")
            if tid and tid not in seen_ids:
                seen_ids.add(tid)
                unique_tracks.append(t)

        random.shuffle(unique_tracks)
        selected = unique_tracks[:limit]

        genre_list = ", ".join(genres)
        header = f"**{mood.title()} Tracks** (genres: {genre_list}):\n\n"
        return header + format_track_list(selected)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_genre_explorer(genre: str, limit: int = 20) -> str:
        """Explore a genre by finding its tracks and artists."""
        limit = max(1, min(30, limit))
        sp = get_client()

        tracks = search_with_pagination(sp, f"genre:{genre}", "track", limit)
        artists = search_with_pagination(sp, f"genre:{genre}", "artist", limit)

        if not tracks and not artists:
            return f"No results found for genre '{genre}'."

        parts = []
        if tracks:
            parts.append("## Tracks\n\n" + format_track_list(tracks))
        if artists:
            parts.append("## Artists\n\n" + format_artist_list(artists))

        return "\n\n".join(parts)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_discover_deep_cuts(artist_id: str, limit: int = 10) -> str:
        """Find an artist's deep cuts -- album tracks that were not released as singles."""
        limit = max(1, min(30, limit))
        sp = get_client()

        source = sp.artist(artist_id)
        source_name = source.get("name", "this artist")

        albums = fetch_artist_albums(sp, artist_id, include_groups="album")
        singles = fetch_artist_albums(sp, artist_id, include_groups="single")

        # Collect single names (lowercased) for filtering
        single_names = set()
        for s in singles:
            name = s.get("name", "")
            if name:
                single_names.add(name.lower())

        # Collect album tracks that aren't singles
        deep_cuts = []
        for album in albums[:5]:
            album_tracks = sp.album_tracks(album["id"])
            for track in album_tracks.get("items", []):
                if track.get("name", "").lower() not in single_names:
                    track["artists"] = album.get("artists", [])
                    track["album"] = {"name": album.get("name", "")}
                    deep_cuts.append(track)

        if not deep_cuts:
            return f"No deep cuts found for {source_name}."

        random.shuffle(deep_cuts)
        selected = deep_cuts[:limit]

        header = f"**Deep Cuts by {source_name}:**\n\n"
        return header + format_track_list(selected)
