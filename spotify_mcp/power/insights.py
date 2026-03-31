"""Listening insights tools — patterns, taste profile, playlist comparison, and freshness."""

import logging
import time
from collections import Counter
from datetime import datetime
from spotipy.exceptions import SpotifyException
from ..utils.spotify_client import get_client, get_artist_cached
from ..utils.pagination import fetch_all_playlist_items
from ..utils.formatting import format_time_distribution, format_genre_chart, ms_to_duration
from ..config import SESSION_GAP_SECONDS
from ..utils.uri_parser import parse_spotify_id

logger = logging.getLogger(__name__)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def register(mcp):

    @mcp.tool()
    def spotify_listening_patterns() -> str:
        """Analyze recent listening patterns: time-of-day, day-of-week, sessions, and repeat plays."""
        sp = get_client()

        try:
            results = sp.current_user_recently_played(limit=50)
        except SpotifyException as e:
            logger.error("Failed to fetch recently played: %s", e)
            return f"**Error:** Could not fetch recently played tracks — {e}"

        items = results.get("items", [])
        if not items:
            return "**Error:** No recently played tracks found."

        # Parse timestamps
        timestamps = []
        track_names = []
        for item in items:
            played_at_str = item.get("played_at", "")
            track = item.get("track", {})
            track_name = track.get("name", "Unknown")
            artists = ", ".join(a["name"] for a in track.get("artists", []))
            track_names.append(f"{track_name} — {artists}")

            try:
                # Spotify returns ISO format like 2026-02-23T14:30:00.000Z
                dt = datetime.fromisoformat(played_at_str.replace("Z", "+00:00"))
                timestamps.append(dt)
            except (ValueError, AttributeError):
                continue

        if not timestamps:
            return "**Error:** Could not parse any play timestamps."

        # Hour-of-day histogram
        hour_counts = Counter(dt.hour for dt in timestamps)

        # Day-of-week distribution
        day_counts = Counter(DAY_NAMES[dt.weekday()] for dt in timestamps)

        # Session detection (gap > 30 minutes = new session)
        sorted_ts = sorted(timestamps)
        sessions = 1
        for i in range(1, len(sorted_ts)):
            gap = (sorted_ts[i] - sorted_ts[i - 1]).total_seconds()
            if gap > SESSION_GAP_SECONDS:
                sessions += 1

        # Repeat/re-listen detection
        track_uri_counts = Counter()
        track_uri_to_name = {}
        for item in items:
            track = item.get("track", {})
            uri = track.get("uri", "")
            if uri:
                track_uri_counts[uri] += 1
                name = track.get("name", "Unknown")
                artists = ", ".join(a["name"] for a in track.get("artists", []))
                track_uri_to_name[uri] = f"{name} — {artists}"

        repeats = {uri: count for uri, count in track_uri_counts.items() if count > 1}

        # Most active hours (top 3)
        top_hours = hour_counts.most_common(3)

        # Build markdown report
        lines = [
            "# Listening Patterns",
            "",
            f"_Based on your last {len(items)} played tracks._",
            "",
            "## Hour-of-Day Distribution",
            "```",
            format_time_distribution(dict(hour_counts)),
            "```",
            "",
            "## Day-of-Week Distribution",
            "",
        ]

        # Day of week in order
        for day in DAY_NAMES:
            count = day_counts.get(day, 0)
            max_day_count = max(day_counts.values()) if day_counts else 0
            bar_len = int((count / max_day_count) * 15) if max_day_count > 0 else 0
            bar = "\u2588" * bar_len
            lines.append(f"- **{day}:** {bar} ({count})")

        lines.append("")
        lines.append("## Sessions")
        lines.append("")
        lines.append(f"- **{sessions}** listening session{'s' if sessions != 1 else ''} detected")
        lines.append(f"- Average tracks per session: **{len(items) / max(sessions, 1):.1f}**")
        lines.append("")

        # Most active hours
        lines.append("## Most Active Hours")
        lines.append("")
        for hour, count in top_hours:
            lines.append(f"- **{hour:02d}:00** — {count} plays")
        lines.append("")

        # Repeats
        if repeats:
            lines.append(f"## Repeat Listens ({len(repeats)} tracks)")
            lines.append("")
            for uri, count in sorted(repeats.items(), key=lambda x: x[1], reverse=True):
                name = track_uri_to_name.get(uri, "Unknown")
                lines.append(f"- **{name}** — played {count}x")
        else:
            lines.append("## Repeat Listens")
            lines.append("")
            lines.append("_No repeated tracks in this window._")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_taste_profile(time_range: str = "medium_term") -> str:
        """Build a genre taste profile with diversity score and niche artist detection from your top artists."""
        valid_ranges = ("short_term", "medium_term", "long_term")
        if time_range not in valid_ranges:
            return f"**Error:** Invalid time_range '{time_range}'. Must be one of: {', '.join(valid_ranges)}"

        sp = get_client()

        try:
            results = sp.current_user_top_artists(limit=50, time_range=time_range)
        except SpotifyException as e:
            logger.error("Failed to fetch top artists: %s", e)
            return f"**Error:** Could not fetch top artists — {e}"

        artists = results.get("items", [])
        if not artists:
            return "**Error:** No top artists found for this time range."

        # Count all genres
        genre_counts = Counter()
        artist_genres = {}  # artist_id -> list of genres
        for artist in artists:
            genres = artist.get("genres", [])
            artist_genres[artist.get("id", "")] = genres
            for genre in genres:
                genre_counts[genre] += 1

        unique_genres = len(genre_counts)
        total_genre_mentions = sum(genre_counts.values())

        # Diversity score
        diversity = unique_genres / max(total_genre_mentions, 1)
        diversity_pct = diversity * 100

        # Identify niche artists: average genre frequency across their genres <= 2
        niche_artists = []
        for artist in artists:
            aid = artist.get("id", "")
            genres = artist_genres.get(aid, [])
            if not genres:
                continue
            avg_freq = sum(genre_counts[g] for g in genres) / len(genres)
            if avg_freq <= 2:
                niche_artists.append(artist)

        # Top 5 genres for summary
        top_5 = [g for g, _ in genre_counts.most_common(5)]

        range_labels = {
            "short_term": "Last 4 Weeks",
            "medium_term": "Last 6 Months",
            "long_term": "All Time",
        }

        # Build markdown report
        lines = [
            "# Your Taste Profile",
            "",
            f"_Based on your top {len(artists)} artists ({range_labels[time_range]})._",
            "",
            "## Your Sound in 5 Genres",
            "",
            f"**{' / '.join(top_5)}**" if top_5 else "_No genre data available._",
            "",
            "## Genre Chart",
            "",
            "```",
            format_genre_chart(dict(genre_counts)),
            "```",
            "",
            "## Diversity Score",
            "",
            f"- **{diversity_pct:.1f}%** genre diversity",
            f"- {unique_genres} unique genres across {total_genre_mentions} total genre tags",
            "",
        ]

        if diversity_pct > 60:
            lines.append("_You have an exceptionally eclectic taste!_")
        elif diversity_pct > 40:
            lines.append("_Your taste is quite diverse — you explore many genres._")
        elif diversity_pct > 20:
            lines.append("_You have a balanced mix of familiar and varied genres._")
        else:
            lines.append("_You have a focused taste — you know what you like._")

        lines.append("")

        # Niche artists
        if niche_artists:
            lines.append(f"## Niche Artists ({len(niche_artists)})")
            lines.append("")
            lines.append("_Artists whose genres are uncommon among your top artists:_")
            lines.append("")
            for artist in niche_artists[:15]:
                name = artist.get("name", "Unknown")
                genres = ", ".join(artist.get("genres", [])[:3])
                if genres:
                    lines.append(f"- **{name}** ({genres})")
                else:
                    lines.append(f"- **{name}**")
        else:
            lines.append("## Niche Artists")
            lines.append("")
            lines.append("_No niche artists detected — your top artists share common genres._")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_playlist_compare(playlist_ids: list[str]) -> str:
        """Compare 2-5 playlists side by side: shared tracks, shared artists, unique tracks, and size/duration."""
        if len(playlist_ids) < 2 or len(playlist_ids) > 5:
            return "**Error:** Please provide between 2 and 5 playlist IDs."

        sp = get_client()

        # Fetch playlist names and tracks
        playlist_names = {}
        playlist_tracks = {}  # pid -> list of track items
        playlist_uris = {}    # pid -> set of track URIs
        playlist_artists = {} # pid -> set of artist IDs
        playlist_artist_names = {}  # artist_id -> name

        for pid in playlist_ids:
            pid = parse_spotify_id(pid)
            try:
                meta = sp.playlist(pid, fields="name")
                playlist_names[pid] = meta.get("name", "Unknown")
            except SpotifyException as e:
                logger.error("Failed to fetch playlist %s: %s", pid, e)
                return f"**Error:** Could not fetch playlist `{pid}` — {e}"

            try:
                items = fetch_all_playlist_items(sp, pid)
                playlist_tracks[pid] = items
            except SpotifyException as e:
                logger.error("Failed to fetch tracks for playlist %s: %s", pid, e)
                return f"**Error:** Could not fetch tracks for playlist `{pid}` — {e}"

            uris = set()
            artist_ids = set()
            for item in items:
                track = item.get("track")
                if not track:
                    continue
                uri = track.get("uri", "")
                if uri:
                    uris.add(uri)
                for artist in track.get("artists", []):
                    aid = artist.get("id", "")
                    if aid:
                        artist_ids.add(aid)
                        playlist_artist_names[aid] = artist.get("name", "Unknown")

            playlist_uris[pid] = uris
            playlist_artists[pid] = artist_ids

        # Normalize playlist_ids to cleaned IDs
        clean_ids = [parse_spotify_id(pid) for pid in playlist_ids]

        # Shared tracks (in ALL playlists)
        if clean_ids:
            shared_uris = set.intersection(*(playlist_uris[pid] for pid in clean_ids))
        else:
            shared_uris = set()

        # Shared artists (in ALL playlists)
        if clean_ids:
            shared_artist_ids = set.intersection(*(playlist_artists[pid] for pid in clean_ids))
        else:
            shared_artist_ids = set()

        # Unique-to-each: tracks in one playlist but not any other
        unique_per_playlist = {}
        for pid in clean_ids:
            other_uris = set()
            for other_pid in clean_ids:
                if other_pid != pid:
                    other_uris |= playlist_uris[other_pid]
            unique_per_playlist[pid] = playlist_uris[pid] - other_uris

        # Build URI-to-name lookup
        uri_to_name = {}
        for pid in clean_ids:
            for item in playlist_tracks[pid]:
                track = item.get("track")
                if not track:
                    continue
                uri = track.get("uri", "")
                name = track.get("name", "Unknown")
                artists = ", ".join(a["name"] for a in track.get("artists", []))
                uri_to_name[uri] = f"{name} — {artists}"

        # Build markdown report
        lines = [
            "# Playlist Comparison",
            "",
        ]

        # Size/duration table
        lines.append("## Overview")
        lines.append("")
        lines.append("| Playlist | Tracks | Duration |")
        lines.append("|----------|--------|----------|")
        for pid in clean_ids:
            name = playlist_names.get(pid, "Unknown")
            track_count = len(playlist_tracks[pid])
            total_ms = 0
            for item in playlist_tracks[pid]:
                track = item.get("track")
                if track:
                    total_ms += track.get("duration_ms", 0)
            duration = ms_to_duration(total_ms)
            lines.append(f"| {name} | {track_count} | {duration} |")
        lines.append("")

        # Shared tracks
        lines.append(f"## Shared Tracks ({len(shared_uris)})")
        lines.append("")
        if shared_uris:
            lines.append("_Tracks that appear in ALL compared playlists:_")
            lines.append("")
            for i, uri in enumerate(sorted(shared_uris)[:25], 1):
                name = uri_to_name.get(uri, "Unknown")
                lines.append(f"{i}. **{name}**")
            if len(shared_uris) > 25:
                lines.append(f"\n_...and {len(shared_uris) - 25} more._")
        else:
            lines.append("_No tracks shared across all playlists._")
        lines.append("")

        # Shared artists
        lines.append(f"## Shared Artists ({len(shared_artist_ids)})")
        lines.append("")
        if shared_artist_ids:
            lines.append("_Artists that appear in ALL compared playlists:_")
            lines.append("")
            sorted_artists = sorted(shared_artist_ids, key=lambda a: playlist_artist_names.get(a, ""))
            for i, aid in enumerate(sorted_artists[:25], 1):
                name = playlist_artist_names.get(aid, "Unknown")
                lines.append(f"{i}. **{name}**")
            if len(shared_artist_ids) > 25:
                lines.append(f"\n_...and {len(shared_artist_ids) - 25} more._")
        else:
            lines.append("_No artists shared across all playlists._")
        lines.append("")

        # Unique to each
        lines.append("## Unique Tracks Per Playlist")
        lines.append("")
        for pid in clean_ids:
            name = playlist_names.get(pid, "Unknown")
            unique = unique_per_playlist.get(pid, set())
            lines.append(f"### {name} ({len(unique)} unique)")
            lines.append("")
            if unique:
                for i, uri in enumerate(sorted(unique)[:10], 1):
                    track_display = uri_to_name.get(uri, "Unknown")
                    lines.append(f"{i}. {track_display}")
                if len(unique) > 10:
                    lines.append(f"\n_...and {len(unique) - 10} more._")
            else:
                lines.append("_No unique tracks — all tracks also appear in other playlists._")
            lines.append("")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_playlist_freshness(owner_only: bool = True, limit: int = 50) -> str:
        """Scan all your playlists and show when each was last updated, sorted by staleness (oldest first)."""
        sp = get_client()
        me = sp.me()
        my_id = me.get("id", "")

        # Fetch all user playlists
        playlists = []
        offset = 0
        while True:
            page = sp.current_user_playlists(limit=50, offset=offset)
            page_items = page.get("items", [])
            playlists.extend(page_items)
            if page.get("next") is None or not page_items:
                break
            offset += 50

        if owner_only:
            playlists = [
                p for p in playlists
                if p.get("owner", {}).get("id") == my_id
            ]

        if not playlists:
            return "No playlists found."

        limit = max(1, min(200, limit))
        now = datetime.utcnow()

        # For each playlist, find the most recent added_at
        freshness = []
        for p in playlists:
            pid = p["id"]
            pname = p.get("name", pid)
            track_count = p.get("tracks", {}).get("total", 0)

            items = fetch_all_playlist_items(sp, pid)
            latest_dt = None
            for item in items:
                added_at_str = item.get("added_at", "")
                if not added_at_str:
                    continue
                try:
                    dt = datetime.fromisoformat(added_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if latest_dt is None or dt > latest_dt:
                        latest_dt = dt
                except (ValueError, AttributeError):
                    continue

            if latest_dt:
                days_ago = (now - latest_dt).days
            else:
                days_ago = -1  # unknown

            freshness.append({
                "name": pname,
                "id": pid,
                "track_count": track_count,
                "last_added": latest_dt,
                "days_ago": days_ago,
            })

        # Sort: unknown dates last, then by days_ago descending (stalest first)
        freshness.sort(key=lambda x: (-1 if x["days_ago"] < 0 else x["days_ago"]), reverse=True)

        lines = [
            "# Playlist Freshness Report",
            "",
            f"Scanned {len(freshness)} playlists"
            + (" (owned by you)" if owner_only else ""),
            "",
        ]

        for i, f in enumerate(freshness[:limit], 1):
            if f["last_added"]:
                date_str = f["last_added"].strftime("%Y-%m-%d")
                if f["days_ago"] == 0:
                    ago = "today"
                elif f["days_ago"] == 1:
                    ago = "1 day ago"
                else:
                    ago = f"{f['days_ago']} days ago"
                lines.append(
                    f"{i}. **{f['name']}** — {f['track_count']} tracks — "
                    f"last added {date_str} ({ago})"
                )
            else:
                lines.append(
                    f"{i}. **{f['name']}** — {f['track_count']} tracks — "
                    f"last added: _unknown_"
                )

        if len(freshness) > limit:
            lines.append(f"\n_...and {len(freshness) - limit} more playlists_")

        # Highlight stale playlists (>180 days)
        stale = [f for f in freshness if f["days_ago"] > 180]
        if stale:
            lines.append("")
            lines.append(f"**{len(stale)} stale playlists** (not updated in 6+ months):")
            for f in stale[:10]:
                lines.append(f"- **{f['name']}** — {f['days_ago']} days ago")
            if len(stale) > 10:
                lines.append(f"_...and {len(stale) - 10} more_")

        return "\n".join(lines)
