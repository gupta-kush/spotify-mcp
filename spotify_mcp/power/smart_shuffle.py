"""Smart shuffle tool — variety-based playlist reordering."""

import logging
from spotipy.exceptions import SpotifyException
from ..utils.spotify_client import get_client, get_artist_cached
from ..utils.pagination import fetch_all_playlist_items
from ..utils.helpers import chunked
from ..config import GENRE_ENERGY_ESTIMATE, API_BATCH_INTERVAL, API_SLEEP_SECONDS

logger = logging.getLogger(__name__)

STRATEGIES = {
    "variety": "Spread same-artist tracks as far apart as possible",
    "alphabetical_artist": "Sort by artist name, then by album within artist",
    "chronological": "Sort by album release date (oldest first)",
    "genre_variety": "Interleave tracks by genre for maximum genre variety",
    "energy_arc": "Arrange tracks in a low→high→low energy arc",
    "reverse_chronological": "Sort by album release date (newest first)",
}


def register(mcp):

    @mcp.tool()
    def spotify_smart_shuffle(
        playlist_id: str,
        strategy: str = "variety",
    ) -> str:
        """Reorder a playlist using a smart strategy: variety, alphabetical_artist, chronological, genre_variety, energy_arc, or reverse_chronological."""
        if strategy not in STRATEGIES:
            available = "\n".join(f"- **{k}**: {v}" for k, v in STRATEGIES.items())
            return f"**Error:** Unknown strategy '{strategy}'. Available:\n{available}"

        sp = get_client()
        playlist_info = sp.playlist(playlist_id, fields="name")
        playlist_name = playlist_info.get("name", "Unknown")

        items = fetch_all_playlist_items(sp, playlist_id)
        if len(items) < 2:
            return f"Playlist '{playlist_name}' has fewer than 2 tracks — nothing to shuffle."

        # Extract valid tracks with their URIs
        tracks = []
        for item in items:
            track = item.get("track")
            if track and track.get("uri"):
                tracks.append(track)

        # Apply strategy
        if strategy == "variety":
            reordered = _variety_shuffle(tracks)
        elif strategy == "alphabetical_artist":
            reordered = _sort_alphabetical(tracks)
        elif strategy == "chronological":
            reordered = _sort_chronological(tracks)
        elif strategy == "genre_variety":
            reordered = _genre_variety_shuffle(sp, tracks)
        elif strategy == "energy_arc":
            reordered = _energy_arc_sort(sp, tracks)
        elif strategy == "reverse_chronological":
            reordered = _sort_reverse_chronological(tracks)

        # Replace playlist contents: clear then re-add
        reordered_uris = [t["uri"] for t in reordered]
        sp.playlist_replace_items(playlist_id, [])  # Clear
        for batch in chunked(reordered_uris, 100):
            sp.playlist_add_items(playlist_id, batch)

        return (
            f"**Smart Shuffled** \"{playlist_name}\" using **{strategy}** strategy.\n"
            f"Reordered {len(reordered)} tracks."
        )


def _variety_shuffle(tracks: list) -> list:
    """Spread same-artist tracks as far apart as possible."""
    # Group by primary artist
    artist_tracks = {}
    for t in tracks:
        artist = t.get("artists", [{}])[0].get("uri", "unknown")
        artist_tracks.setdefault(artist, []).append(t)

    # Sort artists by frequency (most frequent first — they need the most spacing)
    sorted_artists = sorted(
        artist_tracks.keys(),
        key=lambda a: len(artist_tracks[a]),
        reverse=True,
    )

    result = [None] * len(tracks)

    for artist in sorted_artists:
        at = artist_tracks[artist]
        available = [i for i, x in enumerate(result) if x is None]
        if not available:
            break
        step = len(available) / len(at)
        for j, track in enumerate(at):
            idx = available[min(int(j * step), len(available) - 1)]
            result[idx] = track

    # Filter out any None slots (shouldn't happen, but safety)
    return [t for t in result if t is not None]


def _sort_alphabetical(tracks: list) -> list:
    """Sort by primary artist name, then by album name."""
    return sorted(
        tracks,
        key=lambda t: (
            t.get("artists", [{}])[0].get("name", "").lower(),
            t.get("album", {}).get("name", "").lower(),
            t.get("name", "").lower(),
        ),
    )


def _sort_chronological(tracks: list) -> list:
    """Sort by album release date, oldest first."""
    return sorted(
        tracks,
        key=lambda t: t.get("album", {}).get("release_date", "9999"),
    )


def _genre_variety_shuffle(sp, tracks: list) -> list:
    """Group tracks by primary artist genre, then round-robin interleave."""
    import time as _time
    genre_groups = {}
    for i, t in enumerate(tracks):
        artist_id = t.get("artists", [{}])[0].get("id")
        genre = "unknown"
        if artist_id:
            try:
                artist_data = get_artist_cached(sp, artist_id)
                genres = artist_data.get("genres", [])
                if genres:
                    genre = genres[0]
            except SpotifyException:
                pass
            if i > 0 and i % API_BATCH_INTERVAL == 0:
                _time.sleep(API_SLEEP_SECONDS)
        genre_groups.setdefault(genre, []).append(t)

    # Round-robin interleave
    result = []
    groups = list(genre_groups.values())
    max_len = max(len(g) for g in groups) if groups else 0
    for i in range(max_len):
        for group in groups:
            if i < len(group):
                result.append(group[i])
    return result


def _energy_arc_sort(sp, tracks: list) -> list:
    """Sort tracks in a low->high->low energy parabolic arc."""
    import time as _time
    scored = []
    for i, t in enumerate(tracks):
        artist_id = t.get("artists", [{}])[0].get("id")
        energy = 0.5  # default
        if artist_id:
            try:
                artist_data = get_artist_cached(sp, artist_id)
                genres = artist_data.get("genres", [])
                energies = [GENRE_ENERGY_ESTIMATE.get(g, 0.5) for g in genres]
                if energies:
                    energy = sum(energies) / len(energies)
            except SpotifyException:
                pass
            if i > 0 and i % API_BATCH_INTERVAL == 0:
                _time.sleep(API_SLEEP_SECONDS)
        scored.append((energy, t))

    # Sort by energy ascending
    scored.sort(key=lambda x: x[0])

    # Build arc: low->high->low
    # Take sorted list, alternate placing at front and back
    result = [None] * len(scored)
    left, right = 0, len(scored) - 1
    for i, (energy, track) in enumerate(scored):
        if i % 2 == 0:
            result[left] = track
            left += 1
        else:
            result[right] = track
            right -= 1

    return [t for t in result if t is not None]


def _sort_reverse_chronological(tracks: list) -> list:
    """Sort by album release date, newest first."""
    return sorted(
        tracks,
        key=lambda t: t.get("album", {}).get("release_date", "0000"),
        reverse=True,
    )
