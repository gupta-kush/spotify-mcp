"""Listening reports and playlist analysis — 3 tools."""

import logging
import time
from collections import Counter
from spotipy.exceptions import SpotifyException
from ..utils.spotify_client import get_client, get_artist_cached
from ..utils.pagination import fetch_all_playlist_items
from ..utils.formatting import format_track, format_artist, ms_to_duration
from ..config import API_BATCH_INTERVAL, API_SLEEP_SECONDS

logger = logging.getLogger(__name__)

VALID_TIME_RANGES = {
    "short_term": "last 4 weeks",
    "medium_term": "last 6 months",
    "long_term": "all time",
}


def register(mcp):

    @mcp.tool()
    def spotify_listening_report(time_range: str = "medium_term") -> str:
        """Generate a comprehensive listening profile report.

        Combines your top tracks, top artists, genre breakdown, and recent
        listening activity into a single formatted report.

        Args:
            time_range: Time period to analyze.
                        "short_term" = last 4 weeks,
                        "medium_term" = last 6 months (default),
                        "long_term" = all time.
        """
        if time_range not in VALID_TIME_RANGES:
            return f"**Error:** time_range must be one of: {', '.join(VALID_TIME_RANGES.keys())}"

        sp = get_client()
        period = VALID_TIME_RANGES[time_range]

        # Fetch data
        top_artists = sp.current_user_top_artists(time_range=time_range, limit=50)
        top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=50)
        recent = sp.current_user_recently_played(limit=50)

        artists = top_artists.get("items", [])
        tracks = top_tracks.get("items", [])
        recent_items = recent.get("items", [])

        lines = [
            f"# Listening Report ({period})",
            "",
        ]

        # --- Top Artists ---
        lines.append("## Top Artists")
        for i, artist in enumerate(artists[:10], 1):
            lines.append(format_artist(artist, index=i))
        lines.append("")

        # --- Top Tracks ---
        lines.append("## Top Tracks")
        for i, track in enumerate(tracks[:10], 1):
            lines.append(format_track(track, index=i))
        lines.append("")

        # --- Genre Breakdown ---
        genre_counter = Counter()
        for artist in artists:
            for genre in artist.get("genres", []):
                genre_counter[genre] += 1

        if genre_counter:
            lines.append("## Genre Breakdown")
            lines.append("")
            lines.append("| Genre | Count |")
            lines.append("|-------|-------|")
            for genre, count in genre_counter.most_common(15):
                bar = "█" * min(count, 20)
                lines.append(f"| {genre} | {count} {bar} |")
            lines.append("")

        # --- Listening Diversity ---
        unique_artists_recent = len(set(
            item.get("track", {}).get("artists", [{}])[0].get("name", "")
            for item in recent_items
        ))
        lines.append("## Listening Stats")
        lines.append(f"- **Top artists tracked:** {len(artists)}")
        lines.append(f"- **Top tracks tracked:** {len(tracks)}")
        lines.append(f"- **Unique genres:** {len(genre_counter)}")
        lines.append(f"- **Recent unique artists (last 50 plays):** {unique_artists_recent}")

        # Top genre
        if genre_counter:
            top_genre = genre_counter.most_common(1)[0][0]
            lines.append(f"- **Top genre:** {top_genre}")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_playlist_analysis(playlist_id: str) -> str:
        """Analyze a playlist's composition: genres, artists, decades, duration.

        Since Spotify removed audio features from the API, this analysis uses
        artist genres and album release dates instead of danceability/energy/etc.

        Args:
            playlist_id: Spotify playlist ID to analyze.
        """
        sp = get_client()
        playlist_info = sp.playlist(playlist_id, fields="name,tracks.total")
        playlist_name = playlist_info.get("name", "Unknown")

        items = fetch_all_playlist_items(sp, playlist_id)
        if not items:
            return f"Playlist '{playlist_name}' is empty."

        # Collect data
        artist_counter = Counter()
        genre_counter = Counter()
        decade_counter = Counter()
        total_duration_ms = 0
        artist_ids_seen = set()
        artist_ids_to_fetch = []

        for item in items:
            track = item.get("track")
            if not track:
                continue

            total_duration_ms += track.get("duration_ms", 0)

            # Primary artist
            artists = track.get("artists", [])
            if artists:
                primary = artists[0]
                artist_counter[primary.get("name", "Unknown")] += 1
                aid = primary.get("id")
                if aid and aid not in artist_ids_seen:
                    artist_ids_seen.add(aid)
                    artist_ids_to_fetch.append(aid)

            # Decade from album release date
            release_date = track.get("album", {}).get("release_date", "")
            if release_date and len(release_date) >= 4:
                try:
                    year = int(release_date[:4])
                    decade = f"{(year // 10) * 10}s"
                    decade_counter[decade] += 1
                except ValueError:
                    pass

        # Fetch artist genres (with caching, throttled)
        for i, aid in enumerate(artist_ids_to_fetch[:100]):
            try:
                artist_data = get_artist_cached(sp, aid)
                for genre in artist_data.get("genres", []):
                    genre_counter[genre] += 1
            except SpotifyException as e:
                logger.warning(f"Could not fetch artist {aid}: {e}")
            if i > 0 and i % API_BATCH_INTERVAL == 0:
                time.sleep(API_SLEEP_SECONDS)

        if len(artist_ids_to_fetch) > 100:
            logger.info(
                f"Only fetched genres for first 100 of {len(artist_ids_to_fetch)} artists"
            )

        # Build report
        lines = [
            f"# Playlist Analysis: {playlist_name}",
            "",
            f"**Total tracks:** {len(items)}",
            f"**Total duration:** {ms_to_duration(total_duration_ms)}",
            f"**Unique artists:** {len(artist_counter)}",
            "",
        ]

        # Top artists in playlist
        lines.append("## Top Artists")
        lines.append("")
        lines.append("| Artist | Tracks |")
        lines.append("|--------|--------|")
        for artist, count in artist_counter.most_common(15):
            lines.append(f"| {artist} | {count} |")
        lines.append("")

        # Genre distribution
        if genre_counter:
            lines.append("## Genre Distribution")
            lines.append("")
            lines.append("| Genre | Frequency |")
            lines.append("|-------|-----------|")
            for genre, count in genre_counter.most_common(15):
                lines.append(f"| {genre} | {count} |")
            lines.append("")

        # Decade distribution
        if decade_counter:
            lines.append("## Decade Breakdown")
            lines.append("")
            lines.append("| Decade | Tracks |")
            lines.append("|--------|--------|")
            for decade, count in sorted(decade_counter.items()):
                bar = "█" * min(count, 30)
                lines.append(f"| {decade} | {count} {bar} |")
            lines.append("")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_taste_evolution() -> str:
        """Analyze how your music taste has evolved over time.

        Compares your top artists and tracks across three time ranges
        (4 weeks, 6 months, all time) to identify trends.
        """
        sp = get_client()

        periods = {
            "short_term": "Last 4 Weeks",
            "medium_term": "Last 6 Months",
            "long_term": "All Time",
        }

        # Fetch top artists for all periods
        artist_data = {}
        for period_key, period_label in periods.items():
            result = sp.current_user_top_artists(limit=50, time_range=period_key)
            artist_data[period_key] = result.get("items", [])

        # Fetch top tracks for all periods
        track_data = {}
        for period_key, period_label in periods.items():
            result = sp.current_user_top_tracks(limit=50, time_range=period_key)
            track_data[period_key] = result.get("items", [])

        # Artist name sets for comparison
        short_artists = {a["name"] for a in artist_data["short_term"]}
        medium_artists = {a["name"] for a in artist_data["medium_term"]}
        long_artists = {a["name"] for a in artist_data["long_term"]}

        # Consistent favorites (in all 3)
        consistent = short_artists & medium_artists & long_artists

        # Rising (in short but not long)
        rising = short_artists - long_artists

        # Fading (in long but not short)
        fading = long_artists - short_artists

        lines = [
            "# Taste Evolution",
            "",
        ]

        # Consistent favorites
        lines.append("## Consistent Favorites")
        if consistent:
            for name in sorted(consistent)[:15]:
                lines.append(f"- **{name}**")
        else:
            lines.append("_No artists appear across all time periods._")
        lines.append("")

        # Rising artists
        lines.append("## Rising (Recent Discoveries)")
        if rising:
            for name in sorted(rising)[:15]:
                lines.append(f"- **{name}** ↑")
        else:
            lines.append("_No new artists in your recent listening._")
        lines.append("")

        # Fading artists
        lines.append("## Fading (Past Favorites)")
        if fading:
            for name in sorted(fading)[:15]:
                lines.append(f"- **{name}** ↓")
        else:
            lines.append("_No fading artists detected._")
        lines.append("")

        # Genre shift table
        genre_by_period = {}
        for period_key in periods:
            counter = Counter()
            for artist in artist_data[period_key]:
                for genre in artist.get("genres", []):
                    counter[genre] += 1
            genre_by_period[period_key] = counter

        # Get all unique genres across periods, ranked by total
        all_genres = Counter()
        for counter in genre_by_period.values():
            all_genres += counter
        top_genres = [g for g, _ in all_genres.most_common(15)]

        lines.append("## Genre Trends")
        lines.append("")
        lines.append("| Genre | 4 Weeks | 6 Months | All Time | Trend |")
        lines.append("|-------|---------|----------|----------|-------|")
        for genre in top_genres:
            short = genre_by_period["short_term"].get(genre, 0)
            medium = genre_by_period["medium_term"].get(genre, 0)
            long = genre_by_period["long_term"].get(genre, 0)
            if short > long:
                trend = "↑"
            elif short < long:
                trend = "↓"
            else:
                trend = "→"
            lines.append(f"| {genre} | {short} | {medium} | {long} | {trend} |")

        return "\n".join(lines)
