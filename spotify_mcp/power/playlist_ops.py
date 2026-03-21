"""Power tools for playlist operations — 6 tools."""

import logging
from itertools import combinations
from ..utils.spotify_client import get_client
from ..utils.pagination import fetch_all_playlist_items
from ..utils.formatting import format_track, format_track_list, ms_to_duration
from ..utils.helpers import chunked

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    def spotify_deduplicate_playlist(playlist_id: str, dry_run: bool = True) -> str:
        """Find and optionally remove duplicate tracks from a playlist. Set dry_run=False to remove."""
        sp = get_client()
        all_items = fetch_all_playlist_items(sp, playlist_id)

        # Find duplicates
        seen = {}
        duplicates = []
        for i, item in enumerate(all_items):
            track = item.get("track")
            if not track or not track.get("uri"):
                continue
            uri = track["uri"]
            if uri in seen:
                duplicates.append({
                    "name": track.get("name", "Unknown"),
                    "artist": track.get("artists", [{}])[0].get("name", "Unknown"),
                    "uri": uri,
                    "position": i,
                    "first_seen": seen[uri],
                })
            else:
                seen[uri] = i

        if not duplicates:
            return f"No duplicates found in playlist `{playlist_id}` ({len(all_items)} tracks)."

        lines = [
            f"**Duplicate Analysis** for playlist `{playlist_id}`:",
            f"Total tracks: {len(all_items)}",
            f"Duplicates found: {len(duplicates)}",
            "",
        ]

        # Show duplicates
        for i, dup in enumerate(duplicates[:30], 1):
            lines.append(
                f"{i}. **{dup['name']}** by {dup['artist']} "
                f"(position {dup['position']}, first at {dup['first_seen']})"
            )
        if len(duplicates) > 30:
            lines.append(f"\n_...and {len(duplicates) - 30} more duplicates_")

        if dry_run:
            lines.append(
                "\n_Dry run — no changes made. "
                "Call again with `dry_run=False` to remove duplicates._"
            )
        else:
            # Remove duplicate occurrences
            # We need to remove by URI — this removes ALL occurrences, then re-add the first ones
            # Simpler approach: remove specific positions using snapshot
            uris_to_remove = list(set(d["uri"] for d in duplicates))
            positions_to_keep = {}  # uri -> first position

            for uri in uris_to_remove:
                positions_to_keep[uri] = seen[uri]

            # Remove all occurrences then re-add at original positions
            # Actually, a safer approach: remove items by their specific positions
            # The Spotify API supports removing by position with snapshot_id
            playlist_info = sp.playlist(playlist_id, fields="snapshot_id")
            snapshot = playlist_info.get("snapshot_id")

            # Build removal list: {uri, positions} format
            removal_items = []
            for dup in duplicates:
                removal_items.append({
                    "uri": dup["uri"],
                    "positions": [dup["position"]]
                })

            # Remove in batches of 100
            for batch in chunked(removal_items, 100):
                sp.playlist_remove_specific_occurrences_of_items(
                    playlist_id, batch, snapshot_id=snapshot
                )
                # Get new snapshot for next batch
                playlist_info = sp.playlist(playlist_id, fields="snapshot_id")
                snapshot = playlist_info.get("snapshot_id")

            lines.append(f"\nRemoved {len(duplicates)} duplicate track(s).")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_merge_playlists(
        source_playlist_ids: list[str],
        target_name: str,
        deduplicate: bool = True,
    ) -> str:
        """Merge multiple playlists into one new playlist, removing duplicates by default."""
        if len(source_playlist_ids) < 2:
            return "**Error:** Need at least 2 playlist IDs to merge."

        sp = get_client()
        user_id = sp.me()["id"]

        all_uris = []
        seen_uris = set()
        source_names = []
        skipped = 0

        for pid in source_playlist_ids:
            playlist = sp.playlist(pid, fields="name")
            source_names.append(playlist.get("name", pid))

            items = fetch_all_playlist_items(sp, pid)
            for item in items:
                track = item.get("track")
                if not track or not track.get("uri"):
                    continue
                uri = track["uri"]
                if deduplicate and uri in seen_uris:
                    skipped += 1
                    continue
                seen_uris.add(uri)
                all_uris.append(uri)

        if not all_uris:
            return "No tracks found in the source playlists."

        # Create the new playlist
        description = f"Merged from: {', '.join(source_names)}"
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=target_name,
            public=False,
            description=description,
        )
        new_id = new_playlist["id"]

        # Add tracks in batches of 100
        for batch in chunked(all_uris, 100):
            sp.playlist_add_items(new_id, batch)

        lines = [
            f"**Merged Playlist Created:** {target_name}",
            f"ID: `{new_id}`",
            f"Sources: {', '.join(source_names)}",
            f"Total tracks: {len(all_uris)}",
        ]
        if deduplicate and skipped > 0:
            lines.append(f"Duplicates skipped: {skipped}")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_split_playlist_by_artist(playlist_id: str) -> str:
        """Split a playlist into per-artist sub-playlists. Artists with fewer than 3 tracks go into a "Various" playlist."""
        sp = get_client()
        user_id = sp.me()["id"]
        playlist = sp.playlist(playlist_id, fields="name")
        playlist_name = playlist.get("name", "Unknown")

        items = fetch_all_playlist_items(sp, playlist_id)

        # Group tracks by primary artist
        artist_tracks = {}
        for item in items:
            track = item.get("track")
            if not track or not track.get("uri"):
                continue
            artist_name = track.get("artists", [{}])[0].get("name", "Unknown")
            artist_tracks.setdefault(artist_name, []).append(track["uri"])

        # Split into major artists (3+) and various
        major = {k: v for k, v in artist_tracks.items() if len(v) >= 3}
        various_uris = []
        for k, v in artist_tracks.items():
            if len(v) < 3:
                various_uris.extend(v)

        created_playlists = []

        for artist_name, uris in sorted(major.items()):
            name = f"{playlist_name} — {artist_name}"
            new_pl = sp.user_playlist_create(user=user_id, name=name, public=False)
            for batch in chunked(uris, 100):
                sp.playlist_add_items(new_pl["id"], batch)
            created_playlists.append(f"- **{name}** ({len(uris)} tracks)")

        if various_uris:
            name = f"{playlist_name} — Various"
            new_pl = sp.user_playlist_create(user=user_id, name=name, public=False)
            for batch in chunked(various_uris, 100):
                sp.playlist_add_items(new_pl["id"], batch)
            created_playlists.append(f"- **{name}** ({len(various_uris)} tracks)")

        lines = [
            f"**Split \"{playlist_name}\"** into {len(created_playlists)} playlists:",
            "",
        ] + created_playlists

        return "\n".join(lines)

    @mcp.tool()
    def spotify_playlist_diff(playlist_id_a: str, playlist_id_b: str) -> str:
        """Compare two playlists, showing tracks unique to each and tracks they share."""
        sp = get_client()
        pl_a = sp.playlist(playlist_id_a, fields="name")
        pl_b = sp.playlist(playlist_id_b, fields="name")
        name_a = pl_a.get("name", playlist_id_a)
        name_b = pl_b.get("name", playlist_id_b)

        items_a = fetch_all_playlist_items(sp, playlist_id_a)
        items_b = fetch_all_playlist_items(sp, playlist_id_b)

        # Build track maps: uri -> track info
        def build_map(items):
            track_map = {}
            for item in items:
                track = item.get("track")
                if track and track.get("uri"):
                    track_map[track["uri"]] = track
            return track_map

        map_a = build_map(items_a)
        map_b = build_map(items_b)

        uris_a = set(map_a.keys())
        uris_b = set(map_b.keys())

        only_a = uris_a - uris_b
        only_b = uris_b - uris_a
        shared = uris_a & uris_b

        lines = [
            f"**Playlist Comparison:**",
            f"- **{name_a}**: {len(uris_a)} unique tracks",
            f"- **{name_b}**: {len(uris_b)} unique tracks",
            f"- **Shared**: {len(shared)} tracks",
            "",
        ]

        if only_a:
            lines.append(f"**Only in {name_a}** ({len(only_a)}):")
            for i, uri in enumerate(list(only_a)[:20], 1):
                lines.append(format_track(map_a[uri], index=i))
            if len(only_a) > 20:
                lines.append(f"_...and {len(only_a) - 20} more_")
            lines.append("")

        if only_b:
            lines.append(f"**Only in {name_b}** ({len(only_b)}):")
            for i, uri in enumerate(list(only_b)[:20], 1):
                lines.append(format_track(map_b[uri], index=i))
            if len(only_b) > 20:
                lines.append(f"_...and {len(only_b) - 20} more_")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_export_playlist(playlist_id: str) -> str:
        """Export a playlist as a formatted text list with artist, album, and duration for each track."""
        sp = get_client()
        playlist = sp.playlist(playlist_id, fields="name")
        playlist_name = playlist.get("name", "Unknown")

        items = fetch_all_playlist_items(sp, playlist_id)

        lines = [f"# {playlist_name}", f"# {len(items)} tracks", ""]

        total_ms = 0
        for i, item in enumerate(items, 1):
            track = item.get("track")
            if not track:
                continue
            name = track.get("name", "Unknown")
            artists = ", ".join(a["name"] for a in track.get("artists", []))
            album = track.get("album", {}).get("name", "")
            duration_ms = track.get("duration_ms", 0)
            total_ms += duration_ms
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) // 1000
            lines.append(f"{i}. {name} — {artists} [{album}] ({minutes}:{seconds:02d})")

        lines.append("")
        lines.append(f"# Total duration: {ms_to_duration(total_ms)}")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_find_playlist_overlaps(min_shared: int = 1, owner_only: bool = True) -> str:
        """Scan all your playlists and find which pairs share tracks, ranked by overlap."""
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

        if len(playlists) < 2:
            return "Need at least 2 playlists to compare."

        # Fetch track URIs for each playlist
        playlist_tracks = {}
        playlist_names = {}
        for p in playlists:
            pid = p["id"]
            pname = p.get("name", pid)
            playlist_names[pid] = pname
            items = fetch_all_playlist_items(sp, pid)
            uris = set()
            for item in items:
                track = item.get("track")
                if track and track.get("uri"):
                    uris.add(track["uri"])
            playlist_tracks[pid] = uris

        # Compare every pair
        overlaps = []
        for (id_a, id_b) in combinations(playlist_tracks.keys(), 2):
            shared = playlist_tracks[id_a] & playlist_tracks[id_b]
            if len(shared) >= min_shared:
                size_a = len(playlist_tracks[id_a])
                size_b = len(playlist_tracks[id_b])
                # Overlap % relative to smaller playlist
                smaller = min(size_a, size_b)
                pct = (len(shared) / smaller * 100) if smaller > 0 else 0
                overlaps.append({
                    "name_a": playlist_names[id_a],
                    "name_b": playlist_names[id_b],
                    "id_a": id_a,
                    "id_b": id_b,
                    "shared": len(shared),
                    "size_a": size_a,
                    "size_b": size_b,
                    "pct": pct,
                })

        # Sort by shared count descending
        overlaps.sort(key=lambda x: x["shared"], reverse=True)

        lines = [
            f"**Playlist Overlap Scan**",
            f"Scanned {len(playlists)} playlists"
            + (" (owned by you)" if owner_only else ""),
            "",
        ]

        if not overlaps:
            lines.append("No overlapping playlists found.")
            return "\n".join(lines)

        lines.append(f"**{len(overlaps)} pairs with shared tracks** (sorted by overlap):\n")

        for i, o in enumerate(overlaps[:50], 1):
            lines.append(
                f"{i}. **{o['name_a']}** ({o['size_a']} tracks) "
                f"& **{o['name_b']}** ({o['size_b']} tracks) "
                f"— **{o['shared']} shared** ({o['pct']:.0f}% of smaller)"
            )
        if len(overlaps) > 50:
            lines.append(f"\n_...and {len(overlaps) - 50} more pairs_")

        # Highlight strong merge candidates
        strong = [o for o in overlaps if o["pct"] >= 50]
        if strong:
            lines.append("")
            lines.append("**Strong merge candidates** (50%+ overlap of smaller playlist):")
            for o in strong:
                lines.append(
                    f"- **{o['name_a']}** + **{o['name_b']}** "
                    f"({o['shared']} shared, {o['pct']:.0f}%)"
                )

        return "\n".join(lines)
