"""Library index tools — sync, stats, and query for personal music library.

Builds a local JSON index of liked songs and user-created playlists,
enabling AI-powered playlist curation from the user's own music.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ..config import CACHE_DIR
from ..utils.spotify_client import get_client
from ..utils.errors import catch_spotify_errors
from ..utils.pagination import fetch_all_saved_tracks, fetch_all_playlist_items

logger = logging.getLogger(__name__)

LIBRARY_FILE = Path(CACHE_DIR) / "library.json"


def _load_library() -> dict | None:
    """Load library index from disk. Returns None if not found."""
    if not LIBRARY_FILE.exists():
        return None
    try:
        return json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load library index: {e}")
        return None


def _save_library(data: dict):
    """Save library index to disk."""
    LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIBRARY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


def _extract_track(item: dict, source: str, source_name: str = "") -> dict | None:
    """Extract compact track info from a Spotify API item."""
    track = item.get("track")
    if not track or not track.get("id"):
        return None
    artists = [a["name"] for a in track.get("artists", []) if a.get("name")]
    return {
        "track": track.get("name", "Unknown"),
        "artists": artists,
        "album": track.get("album", {}).get("name", "Unknown"),
        "uri": track.get("uri", ""),
        "added_at": item.get("added_at", ""),
        "duration_ms": track.get("duration_ms", 0),
        "source": source,
        "source_name": source_name,
    }


def register(mcp):

    @mcp.tool()
    @catch_spotify_errors
    def spotify_sync_library(
        include_liked: bool = True,
        include_playlists: bool = True,
        force: bool = False,
    ) -> str:
        """Sync your Spotify library to a local index for AI-powered playlist curation.

        Fetches all liked songs and tracks from playlists you created (skips
        followed/saved playlists by others). Run periodically to keep fresh.

        Args:
            include_liked: Sync liked/saved songs. Default True.
            include_playlists: Sync your created playlists. Default True.
            force: Re-sync even if synced recently. Default False.
        """
        # Check if recently synced (within 1 hour) unless forced
        if not force:
            existing = _load_library()
            if existing and existing.get("synced_at"):
                synced = datetime.fromisoformat(existing["synced_at"])
                age_minutes = (datetime.now(timezone.utc) - synced).total_seconds() / 60
                if age_minutes < 60:
                    return (
                        f"Library was synced {int(age_minutes)} minutes ago. "
                        f"Use `force=True` to re-sync.\n\n"
                        f"**Liked songs:** {existing.get('total_liked', 0)} | "
                        f"**Playlists:** {existing.get('total_playlists', 0)} | "
                        f"**Playlist tracks:** {existing.get('total_playlist_tracks', 0)}"
                    )

        sp = get_client()
        user_id = sp.me()["id"]
        data = {
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "liked_songs": [],
            "playlists": [],
            "total_liked": 0,
            "total_playlists": 0,
            "total_playlist_tracks": 0,
        }
        lines = ["**Library Sync**", ""]

        # --- Liked songs ---
        if include_liked:
            logger.info("Syncing liked songs...")
            raw_items = fetch_all_saved_tracks(sp)
            for item in raw_items:
                t = _extract_track(item, "liked")
                if t:
                    data["liked_songs"].append(t)
            data["total_liked"] = len(data["liked_songs"])
            lines.append(f"Liked songs: **{data['total_liked']}**")

        # --- User-created playlists ---
        if include_playlists:
            logger.info("Syncing playlists...")
            # Fetch all user playlists
            all_playlists = []
            offset = 0
            while True:
                page = sp.current_user_playlists(limit=50, offset=offset)
                page_items = page.get("items", [])
                all_playlists.extend(page_items)
                if page.get("next") is None or not page_items:
                    break
                offset += 50

            # Filter to user-owned playlists only
            my_playlists = [
                p for p in all_playlists
                if p.get("owner", {}).get("id") == user_id
            ]
            lines.append(f"Your playlists: **{len(my_playlists)}** (skipped {len(all_playlists) - len(my_playlists)} followed)")

            for pl in my_playlists:
                pl_id = pl["id"]
                pl_name = pl.get("name", "Untitled")
                logger.info(f"  Syncing playlist: {pl_name}")

                raw_items = fetch_all_playlist_items(sp, pl_id)
                tracks = []
                for item in raw_items:
                    t = _extract_track(item, "playlist", pl_name)
                    if t:
                        tracks.append(t)

                # Use earliest track added_at as proxy for playlist creation date
                earliest = ""
                if tracks:
                    dates = [t["added_at"] for t in tracks if t["added_at"]]
                    if dates:
                        earliest = min(dates)

                data["playlists"].append({
                    "name": pl_name,
                    "id": pl_id,
                    "description": pl.get("description", ""),
                    "track_count": len(tracks),
                    "created_at_estimate": earliest,
                    "tracks": tracks,
                })
                data["total_playlist_tracks"] += len(tracks)

            data["total_playlists"] = len(data["playlists"])
            lines.append(f"Playlist tracks: **{data['total_playlist_tracks']}**")

        _save_library(data)
        lines.append("")
        lines.append(f"Saved to `{LIBRARY_FILE}`")
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_library_stats() -> str:
        """Get a summary of your synced library — artist counts, playlist names, and dates.

        Returns your full artist landscape (compact) so the AI can reason about
        vibes, genres, and groupings without loading every track.
        """
        lib = _load_library()
        if not lib:
            return "**Error:** No library index found. Run `spotify_sync_library` first."

        lines = [
            f"**Library synced:** {lib['synced_at'][:10]}",
            f"**Liked songs:** {lib.get('total_liked', 0)} | "
            f"**Playlists:** {lib.get('total_playlists', 0)} | "
            f"**Playlist tracks:** {lib.get('total_playlist_tracks', 0)}",
            "",
        ]

        # --- Artist counts from liked songs ---
        artist_counts_liked = {}
        for t in lib.get("liked_songs", []):
            for a in t.get("artists", []):
                artist_counts_liked[a] = artist_counts_liked.get(a, 0) + 1

        if artist_counts_liked:
            sorted_artists = sorted(artist_counts_liked.items(), key=lambda x: -x[1])
            lines.append(f"**Top Artists — Liked Songs** ({len(sorted_artists)} artists):")
            # Show all artists with counts for full visibility
            artist_strs = [f"{name} ({count})" for name, count in sorted_artists]
            lines.append(" | ".join(artist_strs))
            lines.append("")

        # --- Artist counts from playlists ---
        artist_counts_pl = {}
        for pl in lib.get("playlists", []):
            for t in pl.get("tracks", []):
                for a in t.get("artists", []):
                    artist_counts_pl[a] = artist_counts_pl.get(a, 0) + 1

        if artist_counts_pl:
            sorted_artists = sorted(artist_counts_pl.items(), key=lambda x: -x[1])
            lines.append(f"**Top Artists — Playlists** ({len(sorted_artists)} artists):")
            artist_strs = [f"{name} ({count})" for name, count in sorted_artists]
            lines.append(" | ".join(artist_strs))
            lines.append("")

        # --- Playlist list with metadata ---
        playlists = lib.get("playlists", [])
        if playlists:
            lines.append(f"**Your Playlists ({len(playlists)}):**")
            for pl in playlists:
                created = pl.get("created_at_estimate", "")[:10] or "unknown"
                desc = pl.get("description", "")
                desc_str = f" — {desc}" if desc else ""
                lines.append(
                    f"- **{pl['name']}** ({pl['track_count']} tracks, est. {created}){desc_str}"
                )
            lines.append("")

        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_query_library(
        artists: list[str] = None,
        playlist_name: str = "",
        added_after: str = "",
        added_before: str = "",
        source: str = "all",
        track_name: str = "",
        album_name: str = "",
        limit: int = 200,
    ) -> str:
        """Query your synced library with filters. Returns matching tracks with URIs.

        All filters are combined with AND logic. All text matching is
        case-insensitive and supports partial matches.

        Args:
            artists: Filter by artist names (partial match, case-insensitive).
            playlist_name: Filter to tracks from a specific playlist (partial match).
            added_after: Only tracks added after this date (YYYY-MM-DD).
            added_before: Only tracks added before this date (YYYY-MM-DD).
            source: "liked", "playlists", or "all" (default "all").
            track_name: Filter by track name (partial match).
            album_name: Filter by album name (partial match).
            limit: Max results (default 200, max 500).
        """
        lib = _load_library()
        if not lib:
            return "**Error:** No library index found. Run `spotify_sync_library` first."

        limit = max(1, min(500, limit))

        # Normalize text filters
        artist_filters = [a.lower() for a in (artists or [])]
        playlist_filter = playlist_name.lower().strip()
        track_filter = track_name.lower().strip()
        album_filter = album_name.lower().strip()

        # Parse date filters
        date_after = None
        date_before = None
        if added_after:
            try:
                date_after = datetime.fromisoformat(added_after)
            except ValueError:
                return f"**Error:** Invalid date format for added_after: `{added_after}`. Use YYYY-MM-DD."
        if added_before:
            try:
                date_before = datetime.fromisoformat(added_before)
            except ValueError:
                return f"**Error:** Invalid date format for added_before: `{added_before}`. Use YYYY-MM-DD."

        # Collect candidate tracks
        candidates = []

        if source in ("liked", "all"):
            for t in lib.get("liked_songs", []):
                candidates.append(t)

        if source in ("playlists", "all"):
            for pl in lib.get("playlists", []):
                # If playlist_name filter is set, only include matching playlists
                if playlist_filter and playlist_filter not in pl.get("name", "").lower():
                    continue
                for t in pl.get("tracks", []):
                    candidates.append(t)

        # Apply filters
        results = []
        seen_uris = set()  # deduplicate across sources

        for t in candidates:
            uri = t.get("uri", "")
            if uri in seen_uris:
                continue

            # Artist filter: track must match at least one requested artist
            if artist_filters:
                track_artists = [a.lower() for a in t.get("artists", [])]
                if not any(
                    any(af in ta for ta in track_artists)
                    for af in artist_filters
                ):
                    continue

            # Track name filter
            if track_filter and track_filter not in t.get("track", "").lower():
                continue

            # Album name filter
            if album_filter and album_filter not in t.get("album", "").lower():
                continue

            # Date filters
            added = t.get("added_at", "")
            if added and (date_after or date_before):
                try:
                    track_date = datetime.fromisoformat(added.replace("Z", "+00:00"))
                    if date_after and track_date < date_after.replace(tzinfo=track_date.tzinfo):
                        continue
                    if date_before and track_date > date_before.replace(tzinfo=track_date.tzinfo):
                        continue
                except ValueError:
                    pass  # skip date filtering for malformed dates

            seen_uris.add(uri)
            results.append(t)

            if len(results) >= limit:
                break

        if not results:
            return "No tracks found matching your filters."

        # Format output
        lines = [f"**Found {len(results)} tracks:**", ""]
        for i, t in enumerate(results, 1):
            artists_str = ", ".join(t.get("artists", ["Unknown"]))
            added = t.get("added_at", "")[:10]
            src = t.get("source", "")
            src_name = t.get("source_name", "")
            if src == "playlist" and src_name:
                src_label = f"playlist: {src_name}"
            else:
                src_label = src
            lines.append(
                f"{i}. **{t['track']}** — {artists_str} "
                f"({t.get('album', '')}) [{src_label}, {added}]"
            )

        # Append URIs block for easy copy into playlist creation
        lines.append("")
        lines.append("**URIs:**")
        uris = [t["uri"] for t in results if t.get("uri")]
        lines.append(", ".join(uris))

        return "\n".join(lines)
