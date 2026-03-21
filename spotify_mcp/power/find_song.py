"""Natural language song finder — parse descriptions into structured Spotify queries."""

import logging
import re
from spotipy.exceptions import SpotifyException
from ..utils.spotify_client import get_client
from ..utils.pagination import search_with_pagination
from ..utils.formatting import format_track_list
from ..config import DECADE_RANGES

logger = logging.getLogger(__name__)

# Genres to detect in free-text descriptions
_KNOWN_GENRES = {
    "rock", "pop", "jazz", "hip-hop", "electronic", "metal",
    "folk", "country", "classical", "r&b", "soul", "punk",
    "indie", "blues", "latin", "reggae",
}

# Word-form decade aliases → canonical key in DECADE_RANGES
_DECADE_WORDS = {
    "sixties": "1960s", "seventies": "1970s", "eighties": "1980s",
    "nineties": "1990s", "two-thousands": "2000s", "twenty-tens": "2010s",
    "twenty-twenties": "2020s",
}

# Prepositions that stop an artist-name capture
_STOP_WORDS = {"in", "from", "that", "with", "about", "on", "during", "like"}


def _parse_description(description: str) -> dict:
    """Parse heuristics from a natural-language song description.

    Extracts:
        - Quoted text as a title
        - ``by {name}`` or ``from {name}`` as an artist
        - Decade references (``90s``, ``1990s``, ``nineties``) → year range
        - Genre keywords from a known set

    Returns:
        dict with keys title, artist, year_range, genre (all optional, None if
        not found).
    """
    title = None
    artist = None
    year_range = None
    genre = None

    # --- title: extract first "quoted text" ---
    quoted = re.search(r'"([^"]+)"', description)
    if quoted:
        title = quoted.group(1)

    # --- artist: "by {name}" or "from {name}" ---
    artist_match = re.search(
        r'\b(?:by|from)\s+([A-Z][^\n,]+)', description, re.IGNORECASE,
    )
    if artist_match:
        raw_artist = artist_match.group(1).strip()
        # Stop at common prepositions
        words = raw_artist.split()
        cleaned = []
        for w in words:
            if w.lower() in _STOP_WORDS:
                break
            cleaned.append(w)
        if cleaned:
            artist = " ".join(cleaned)

    # --- decade / year range ---
    # Numeric forms: "90s", "1990s"
    decade_match = re.search(r'\b(\d{2,4})s\b', description, re.IGNORECASE)
    if decade_match:
        raw = decade_match.group(1)
        # Normalise short form: "90" -> "1990"
        if len(raw) == 2:
            century = "19" if int(raw) >= 30 else "20"
            raw = century + raw
        key = raw + "s"  # e.g. "1990s"
        year_range = DECADE_RANGES.get(key)

    # Word forms: "nineties", "eighties", etc.
    if year_range is None:
        lower = description.lower()
        for word, key in _DECADE_WORDS.items():
            if word in lower:
                year_range = DECADE_RANGES.get(key)
                break

    # --- genre ---
    lower_words = set(re.findall(r'[\w&-]+', description.lower()))
    for g in _KNOWN_GENRES:
        if g in lower_words:
            genre = g
            break

    return {
        "title": title,
        "artist": artist,
        "year_range": year_range,
        "genre": genre,
    }


def register(mcp):

    @mcp.tool()
    def spotify_find_song(description: str, limit: int = 10) -> str:
        """Find songs using a natural-language description. Parses quoted titles, "by artist", decade refs, and genre keywords."""
        try:
            sp = get_client()
            limit = max(1, min(20, limit))

            parsed = _parse_description(description)
            logger.info("Parsed description: %s", parsed)

            # --- build structured query ---
            parts = []
            if parsed["title"]:
                parts.append(f'track:{parsed["title"]}')
            if parsed["artist"]:
                parts.append(f'artist:{parsed["artist"]}')
            if parsed["year_range"]:
                parts.append(f'year:{parsed["year_range"]}')
            if parsed["genre"]:
                parts.append(f'genre:{parsed["genre"]}')

            structured_query = " ".join(parts) if parts else None

            # --- run structured search ---
            structured_results = []
            if structured_query:
                logger.info("Structured query: %s", structured_query)
                structured_results = search_with_pagination(
                    sp, structured_query, "track", limit,
                )

            # --- run backup raw search ---
            raw_results = search_with_pagination(
                sp, description, "track", limit,
            )

            # --- combine & deduplicate by track ID ---
            seen_ids = set()
            combined = []
            for track in structured_results + raw_results:
                tid = track.get("id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    combined.append(track)

            results = combined[:limit]

            # --- format parsed info header ---
            parsed_parts = []
            if parsed["title"]:
                parsed_parts.append(f'title="{parsed["title"]}"')
            if parsed["artist"]:
                parsed_parts.append(f'artist="{parsed["artist"]}"')
            if parsed["year_range"]:
                parsed_parts.append(f'year={parsed["year_range"]}')
            if parsed["genre"]:
                parsed_parts.append(f'genre={parsed["genre"]}')

            header = "**Parsed:** " + (", ".join(parsed_parts) if parsed_parts else "_no structured fields detected_")
            track_list = format_track_list(results)

            return f"{header}\n\n{track_list}"

        except SpotifyException as exc:
            logger.error("spotify_find_song failed: %s", exc)
            return f"**Error:** {exc}"
