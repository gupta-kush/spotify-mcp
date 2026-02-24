"""Smart playlist generation — 4 tools for creating playlists from seeds, moods, eras, and listening history."""

import logging
import random
from datetime import datetime
from ..utils.spotify_client import get_client
from ..utils.pagination import search_with_pagination, fetch_artist_albums
from ..utils.formatting import format_track_list
from ..utils.uri_parser import parse_spotify_id
from ..config import MOOD_GENRE_MAP, DECADE_RANGES
from ..utils.helpers import chunked

logger = logging.getLogger(__name__)


def _deduplicate_tracks(tracks):
    """Remove duplicate tracks by track ID, preserving order."""
    seen = set()
    result = []
    for track in tracks:
        tid = track.get("id")
        if tid and tid not in seen:
            seen.add(tid)
            result.append(track)
    return result


def _create_and_populate(sp, name, description, uris):
    """Create a private playlist and batch-add tracks in chunks of 100.

    Returns a formatted markdown result string.
    """
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description=description,
    )
    playlist_id = playlist["id"]
    playlist_url = playlist.get("external_urls", {}).get("spotify", "")

    for batch in chunked(uris, 100):
        sp.playlist_add_items(playlist_id, batch)

    lines = [
        f"**Playlist Created:** {name}",
        f"ID: `{playlist_id}`",
    ]
    if playlist_url:
        lines.append(f"URL: {playlist_url}")
    lines.append(f"Tracks: {len(uris)}")
    lines.append(f"_{description}_")
    return "\n".join(lines)


def register(mcp):

    @mcp.tool()
    def spotify_create_radio(
        seed_uri: str,
        name: str = None,
        limit: int = 30,
    ) -> str:
        """Create a radio-style playlist from a seed track or artist.

        Builds the playlist by finding related artists, sampling their recent
        albums, and collecting tracks — similar to Spotify's radio feature.

        Args:
            seed_uri: Spotify URI or ID for a track or artist.
                      Examples: "spotify:track:4uLU6...", "spotify:artist:0OdUW...",
                      or just the raw ID (treated as a track).
            name: Custom playlist name. Defaults to "{Artist} Radio".
            limit: Number of tracks (1-50). Default 30.
        """
        limit = max(1, min(50, limit))
        sp = get_client()

        try:
            # Determine the seed artist
            seed_id = parse_spotify_id(seed_uri)
            artist_id = None
            artist_name = None

            if "artist" in seed_uri:
                artist_id = seed_id
                artist_info = sp.artist(artist_id)
                artist_name = artist_info.get("name", "Unknown")
            else:
                # Treat as track — get the track to find the primary artist
                track_info = sp.track(seed_id)
                artists = track_info.get("artists", [])
                if not artists:
                    return "**Error:** Could not determine artist from seed track."
                artist_id = artists[0].get("id")
                artist_name = artists[0].get("name", "Unknown")

            if not artist_id:
                return "**Error:** Could not resolve artist from the provided seed."

            # Get related artists
            related = sp.artist_related_artists(artist_id)
            related_artists = related.get("artists", [])

            # Build artist pool: seed + up to 7 related artists
            artist_pool = [{"id": artist_id, "name": artist_name}]
            sampled_related = random.sample(
                related_artists,
                min(7, len(related_artists)),
            )
            for ra in sampled_related:
                artist_pool.append({"id": ra["id"], "name": ra.get("name", "Unknown")})

            # Collect tracks from each artist's most recent album
            collected_tracks = []
            for artist in artist_pool:
                try:
                    albums = fetch_artist_albums(sp, artist["id"], include_groups="album,single")
                    if not albums:
                        continue

                    # Sort by release date, newest first
                    albums.sort(
                        key=lambda a: a.get("release_date", ""),
                        reverse=True,
                    )

                    # Pick the most recent album
                    recent_album = albums[0]
                    album_tracks = sp.album_tracks(recent_album["id"], limit=5)
                    for t in album_tracks.get("items", []):
                        # Album tracks lack full track info — enrich with album/artist context
                        t["album"] = {
                            "name": recent_album.get("name", ""),
                            "release_date": recent_album.get("release_date", ""),
                        }
                        if "artists" not in t or not t["artists"]:
                            t["artists"] = [{"name": artist["name"]}]
                        collected_tracks.append(t)
                except Exception as e:
                    logger.warning(f"Error fetching tracks for artist {artist['name']}: {e}")
                    continue

            if not collected_tracks:
                return "**Error:** Could not collect any tracks from related artists."

            # Shuffle, deduplicate, trim
            random.shuffle(collected_tracks)
            collected_tracks = _deduplicate_tracks(collected_tracks)
            collected_tracks = collected_tracks[:limit]

            uris = [t["uri"] for t in collected_tracks if t.get("uri")]
            if not uris:
                return "**Error:** No valid track URIs collected."

            playlist_name = name if name else f"{artist_name} Radio"
            description = f"Radio playlist seeded from {artist_name} and related artists"

            result = _create_and_populate(sp, playlist_name, description, uris)

            # Append a preview of what's in the playlist
            lines = [result, "", "**Track Preview:**"]
            for i, track in enumerate(collected_tracks[:10], 1):
                t_name = track.get("name", "Unknown")
                t_artist = track.get("artists", [{}])[0].get("name", "Unknown")
                lines.append(f"{i}. **{t_name}** by {t_artist}")
            if len(collected_tracks) > 10:
                lines.append(f"_...and {len(collected_tracks) - 10} more_")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"spotify_create_radio failed: {e}")
            return f"**Error:** {e}"

    @mcp.tool()
    def spotify_time_capsule(
        time_range: str = "medium_term",
        name: str = None,
    ) -> str:
        """Create a playlist snapshot of your current top tracks.

        Captures your most-played tracks into a private playlist — a musical
        time capsule you can revisit later to remember what you were listening to.

        Args:
            time_range: Listening period to capture.
                        "short_term" = last 4 weeks,
                        "medium_term" = last 6 months (default),
                        "long_term" = all time.
            name: Custom playlist name. Defaults to "My Time Capsule (Mon YYYY — period)".
        """
        valid_ranges = {
            "short_term": "4 weeks",
            "medium_term": "6 months",
            "long_term": "all time",
        }

        if time_range not in valid_ranges:
            available = ", ".join(f"`{k}` ({v})" for k, v in valid_ranges.items())
            return f"**Error:** Invalid time_range. Choose from: {available}"

        sp = get_client()

        try:
            label = valid_ranges[time_range]
            top = sp.current_user_top_tracks(limit=50, time_range=time_range)
            tracks = top.get("items", [])

            if not tracks:
                return f"**Error:** No top tracks found for {label}. Listen to more music first!"

            uris = [t["uri"] for t in tracks if t.get("uri")]
            if not uris:
                return "**Error:** No valid track URIs found in your top tracks."

            playlist_name = name if name else (
                f"My Time Capsule ({datetime.now().strftime('%b %Y')} — {label})"
            )
            description = (
                f"Time capsule of my top {len(uris)} tracks "
                f"({label}, captured {datetime.now().strftime('%Y-%m-%d')})"
            )

            result = _create_and_populate(sp, playlist_name, description, uris)

            # Append track listing
            lines = [result, "", "**Your Top Tracks:**"]
            lines.append(format_track_list(tracks))

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"spotify_time_capsule failed: {e}")
            return f"**Error:** {e}"

    @mcp.tool()
    def spotify_vibe_playlist(
        mood: str,
        name: str = None,
        limit: int = 30,
    ) -> str:
        """Create a playlist matching a specific mood or vibe.

        Searches across mood-associated genres to build a thematic playlist.

        Args:
            mood: Target mood/vibe. Available moods:
                  happy, sad, energetic, chill, focused, romantic, angry, party.
            name: Custom playlist name. Defaults to "{Mood} Vibes".
            limit: Number of tracks (1-50). Default 30.
        """
        limit = max(1, min(50, limit))
        mood_lower = mood.lower().strip()

        if mood_lower not in MOOD_GENRE_MAP:
            available = ", ".join(f"`{k}`" for k in sorted(MOOD_GENRE_MAP.keys()))
            return f"**Error:** Unknown mood '{mood}'. Available moods: {available}"

        sp = get_client()

        try:
            genres = MOOD_GENRE_MAP[mood_lower]
            collected_tracks = []

            # Search across all genres for the mood
            tracks_per_genre = max(1, (limit * 2) // len(genres))
            for genre in genres:
                query = f"genre:{genre}"
                results = search_with_pagination(
                    sp, query, "track", total_desired=tracks_per_genre,
                )
                collected_tracks.extend(results)

            if not collected_tracks:
                return f"**Error:** No tracks found for mood '{mood}'. Try a different mood."

            # Deduplicate, shuffle, trim
            collected_tracks = _deduplicate_tracks(collected_tracks)
            random.shuffle(collected_tracks)
            collected_tracks = collected_tracks[:limit]

            uris = [t["uri"] for t in collected_tracks if t.get("uri")]
            if not uris:
                return "**Error:** No valid track URIs collected."

            playlist_name = name if name else f"{mood.title()} Vibes"
            description = (
                f"{mood.title()} mood playlist — "
                f"genres: {', '.join(genres)}"
            )

            result = _create_and_populate(sp, playlist_name, description, uris)

            # Append track preview
            lines = [result, "", "**Track Preview:**"]
            lines.append(format_track_list(collected_tracks[:15]))

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"spotify_vibe_playlist failed: {e}")
            return f"**Error:** {e}"

    @mcp.tool()
    def spotify_era_playlist(
        decade: str,
        name: str = None,
        limit: int = 30,
    ) -> str:
        """Create a playlist of tracks from a specific decade.

        Searches for tracks released within the given decade's year range.

        Args:
            decade: Target decade. Available decades:
                    1960s, 1970s, 1980s, 1990s, 2000s, 2010s, 2020s.
            name: Custom playlist name. Defaults to "{Decade} Mix".
            limit: Number of tracks (1-50). Default 30.
        """
        limit = max(1, min(50, limit))
        decade_key = decade.strip()

        if decade_key not in DECADE_RANGES:
            available = ", ".join(f"`{k}`" for k in sorted(DECADE_RANGES.keys()))
            return f"**Error:** Unknown decade '{decade}'. Available decades: {available}"

        sp = get_client()

        try:
            year_range = DECADE_RANGES[decade_key]
            query = f"year:{year_range}"

            # Fetch more than needed so we have variety after deduplication
            collected_tracks = search_with_pagination(
                sp, query, "track", total_desired=limit * 3,
            )

            if not collected_tracks:
                return f"**Error:** No tracks found for decade '{decade}'. Try a different decade."

            # Deduplicate, shuffle, trim
            collected_tracks = _deduplicate_tracks(collected_tracks)
            random.shuffle(collected_tracks)
            collected_tracks = collected_tracks[:limit]

            uris = [t["uri"] for t in collected_tracks if t.get("uri")]
            if not uris:
                return "**Error:** No valid track URIs collected."

            playlist_name = name if name else f"{decade_key} Mix"
            description = f"Tracks from the {decade_key} ({year_range})"

            result = _create_and_populate(sp, playlist_name, description, uris)

            # Append track preview
            lines = [result, "", "**Track Preview:**"]
            lines.append(format_track_list(collected_tracks[:15]))

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"spotify_era_playlist failed: {e}")
            return f"**Error:** {e}"
