"""Vibe engine tools — genre-based vibe analysis for playlists.

Since audio features are unavailable (removed Feb 2026), these tools
estimate playlist mood and energy from artist genre data and curated
energy mappings.
"""

import logging
import random
import time
from collections import Counter

from ..utils.spotify_client import get_client, get_artist_cached
from ..utils.pagination import fetch_all_playlist_items, search_with_pagination
from ..utils.formatting import format_track_list, format_genre_chart
from ..utils.uri_parser import parse_spotify_id
from ..config import GENRE_CLUSTERS, GENRE_ENERGY_ESTIMATE, API_BATCH_INTERVAL, API_SLEEP_SECONDS

logger = logging.getLogger(__name__)


def _estimate_energy(genres: list) -> float:
    """Average energy estimate from GENRE_ENERGY_ESTIMATE for matching genres.

    Args:
        genres: List of genre strings from artist data.

    Returns:
        Average energy as a float between 0 and 1. Defaults to 0.5 if
        no genres match the energy lookup table.
    """
    matched = [
        GENRE_ENERGY_ESTIMATE[g]
        for g in genres
        if g in GENRE_ENERGY_ESTIMATE
    ]
    if not matched:
        # Also try substring matching for compound genres like "indie rock"
        for genre in genres:
            for key, energy in GENRE_ENERGY_ESTIMATE.items():
                if key in genre:
                    matched.append(energy)
                    break  # one match per genre is enough
    if not matched:
        return 0.5
    return sum(matched) / len(matched)


def _determine_vibe(energy: float, genre_counts: Counter) -> str:
    """Determine a vibe label based on energy level and dominant genres.

    Args:
        energy: Estimated energy level (0.0 to 1.0).
        genre_counts: Counter of genre frequencies.

    Returns:
        A descriptive vibe label string.
    """
    # Determine base vibe from energy
    if energy > 0.8:
        label = "High Energy"
    elif energy > 0.65:
        label = "Upbeat"
    elif energy > 0.45:
        label = "Balanced"
    elif energy > 0.3:
        label = "Chill"
    else:
        label = "Melancholic"

    # Check for eclecticism: count how many distinct clusters the top genres span
    top_genres = [g for g, _ in genre_counts.most_common(20)]
    clusters_hit = set()
    for genre in top_genres:
        for cluster_name, cluster_keywords in GENRE_CLUSTERS.items():
            for keyword in cluster_keywords:
                if keyword in genre:
                    clusters_hit.add(cluster_name)
                    break

    if len(clusters_hit) >= 5:
        label = "Eclectic " + label

    return label


def register(mcp):

    @mcp.tool()
    def spotify_playlist_vibe(playlist_id: str) -> str:
        """Analyze a playlist's vibe based on artist genres.

        Since Spotify audio features are no longer available, this uses
        artist genre data and curated energy estimates to determine the
        overall mood, energy, and genre makeup of a playlist.

        Args:
            playlist_id: Spotify playlist ID or URI.
        """
        sp = get_client()
        playlist_id = parse_spotify_id(playlist_id)

        try:
            playlist_info = sp.playlist(playlist_id, fields="name,tracks.total")
        except Exception as e:
            logger.error("Failed to fetch playlist %s: %s", playlist_id, e)
            return f"**Error:** Could not fetch playlist — {e}"

        playlist_name = playlist_info.get("name", "Unknown")
        items = fetch_all_playlist_items(sp, playlist_id)

        if not items:
            return f"**Error:** Playlist '{playlist_name}' is empty."

        # Extract unique artist IDs from all tracks
        artist_ids = set()
        track_count = 0
        for item in items:
            track = item.get("track")
            if not track:
                continue
            track_count += 1
            for artist in track.get("artists", []):
                aid = artist.get("id")
                if aid:
                    artist_ids.add(aid)

        if not artist_ids:
            return f"**Error:** No artist data found in playlist '{playlist_name}'."

        # Cap at 100 artists to avoid excessive API calls
        artist_ids_list = list(artist_ids)[:100]
        logger.info(
            "Fetching genre data for %d artists (capped from %d)",
            len(artist_ids_list), len(artist_ids),
        )

        # Batch fetch genres via cached artist lookups with throttling
        all_genres = []
        genre_counts = Counter()
        for i, aid in enumerate(artist_ids_list):
            try:
                artist_data = get_artist_cached(sp, aid)
                genres = artist_data.get("genres", [])
                all_genres.extend(genres)
                genre_counts.update(genres)
            except Exception as e:
                logger.warning("Failed to fetch artist %s: %s", aid, e)

            # Throttle to avoid rate limits
            if (i + 1) % API_BATCH_INTERVAL == 0:
                time.sleep(API_SLEEP_SECONDS)

        if not all_genres:
            return (
                f"## Vibe Analysis: {playlist_name}\n\n"
                f"**Tracks:** {track_count}\n\n"
                f"_No genre data available for any artists in this playlist._"
            )

        # Cluster genres into broad categories
        cluster_counts = Counter()
        for genre, count in genre_counts.items():
            for cluster_name, cluster_keywords in GENRE_CLUSTERS.items():
                for keyword in cluster_keywords:
                    if keyword in genre:
                        cluster_counts[cluster_name] += count
                        break

        # Estimate energy and determine vibe
        energy = _estimate_energy(list(genre_counts.keys()))
        vibe = _determine_vibe(energy, genre_counts)

        # Vibe descriptions
        vibe_descriptions = {
            "High Energy": "This playlist is packed with intense, high-energy tracks.",
            "Upbeat": "An upbeat playlist with a positive, driving feel.",
            "Balanced": "A well-rounded playlist mixing energy with mellower moments.",
            "Chill": "A relaxed, laid-back playlist for winding down.",
            "Melancholic": "A contemplative, atmospheric playlist with a softer tone.",
        }
        # Handle "Eclectic" prefix
        base_vibe = vibe.replace("Eclectic ", "")
        description = vibe_descriptions.get(base_vibe, "A unique mix of sounds.")
        if vibe.startswith("Eclectic"):
            description = "A wide-ranging, genre-spanning collection. " + description

        # Build the report
        lines = [
            f"## Vibe Analysis: {playlist_name}",
            "",
            f"**Tracks:** {track_count} | **Artists analyzed:** {len(artist_ids_list)} | **Unique genres:** {len(genre_counts)}",
            "",
            f"### Vibe: {vibe}",
            "",
            description,
            "",
            f"**Estimated Energy:** {energy:.0%}",
            "",
            "### Top Genres",
            "",
            format_genre_chart(dict(genre_counts)),
            "",
        ]

        if cluster_counts:
            lines.append("### Genre Clusters")
            lines.append("")
            sorted_clusters = sorted(cluster_counts.items(), key=lambda x: x[1], reverse=True)
            for cluster_name, count in sorted_clusters:
                bar_len = int((count / sorted_clusters[0][1]) * 15)
                bar = "\u2588" * bar_len
                lines.append(f"- **{cluster_name}**  {bar}  ({count})")
            lines.append("")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_find_vibe_matches(
        source_playlist_id: str,
        limit: int = 20,
    ) -> str:
        """Find tracks that match a playlist's vibe based on its genre profile.

        Analyzes the source playlist's genre makeup and searches for tracks
        in those genres that are not already in the playlist.

        Args:
            source_playlist_id: Spotify playlist ID or URI of the source playlist.
            limit: Number of matching tracks to return (1-30, default 20).
        """
        sp = get_client()
        limit = max(1, min(30, limit))
        source_playlist_id = parse_spotify_id(source_playlist_id)

        try:
            playlist_info = sp.playlist(source_playlist_id, fields="name")
        except Exception as e:
            logger.error("Failed to fetch playlist %s: %s", source_playlist_id, e)
            return f"**Error:** Could not fetch playlist — {e}"

        playlist_name = playlist_info.get("name", "Unknown")
        items = fetch_all_playlist_items(sp, source_playlist_id)

        if not items:
            return f"**Error:** Playlist '{playlist_name}' is empty."

        # Collect existing track IDs to filter them out later
        existing_track_ids = set()
        artist_ids = set()
        for item in items:
            track = item.get("track")
            if not track:
                continue
            tid = track.get("id")
            if tid:
                existing_track_ids.add(tid)
            for artist in track.get("artists", []):
                aid = artist.get("id")
                if aid:
                    artist_ids.add(aid)

        if not artist_ids:
            return f"**Error:** No artist data found in playlist '{playlist_name}'."

        # Fetch genres from artists (cap at 100)
        artist_ids_list = list(artist_ids)[:100]
        genre_counts = Counter()
        for i, aid in enumerate(artist_ids_list):
            try:
                artist_data = get_artist_cached(sp, aid)
                genres = artist_data.get("genres", [])
                genre_counts.update(genres)
            except Exception as e:
                logger.warning("Failed to fetch artist %s: %s", aid, e)
            if (i + 1) % API_BATCH_INTERVAL == 0:
                time.sleep(API_SLEEP_SECONDS)

        if not genre_counts:
            return f"**Error:** No genre data available for artists in '{playlist_name}'."

        # Take top 5 genres for searching
        top_genres = [g for g, _ in genre_counts.most_common(5)]
        logger.info("Searching for vibe matches using top genres: %s", top_genres)

        # Distribute limit across genres, ensuring at least a few per genre
        per_genre_limit = max(5, limit // len(top_genres) + 2)

        # Search for tracks in each genre
        candidates = []
        seen_ids = set()
        for genre in top_genres:
            try:
                results = search_with_pagination(
                    sp, f"genre:{genre}", "track", per_genre_limit,
                )
                for track in results:
                    tid = track.get("id")
                    if tid and tid not in existing_track_ids and tid not in seen_ids:
                        seen_ids.add(tid)
                        candidates.append(track)
            except Exception as e:
                logger.warning("Search failed for genre '%s': %s", genre, e)

        if not candidates:
            return (
                f"**Error:** Could not find any matching tracks for the vibe of "
                f"'{playlist_name}'. Try a playlist with more mainstream genres."
            )

        # Shuffle and take the requested number
        random.shuffle(candidates)
        matches = candidates[:limit]

        lines = [
            f"## Vibe Matches for: {playlist_name}",
            "",
            f"Based on top genres: {', '.join(top_genres)}",
            f"Found **{len(matches)}** tracks that match the vibe:",
            "",
            format_track_list(matches),
        ]

        return "\n".join(lines)
