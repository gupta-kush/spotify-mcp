"""Playlist curation power tools — cleanup, interleave, and radio generation."""

import logging
import random
from ..utils.spotify_client import get_client
from ..utils.pagination import fetch_all_playlist_items, fetch_artist_albums
from ..utils.formatting import format_track_list
from ..utils.helpers import chunked

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    def spotify_cleanup_playlist(
        playlist_id: str,
        remove_unavailable: bool = True,
        remove_duplicates: bool = True,
        dry_run: bool = True,
    ) -> str:
        """Find and optionally remove unavailable and duplicate tracks from a playlist.

        Scans the entire playlist for tracks that are no longer playable and
        for duplicate entries (by Spotify URI, keeping the first occurrence).

        Args:
            playlist_id: Spotify playlist ID or URI.
            remove_unavailable: If True, include unavailable/unplayable tracks in cleanup.
            remove_duplicates: If True, include duplicate tracks in cleanup.
            dry_run: If True (default), only reports findings without making changes.
                     Set to False to actually remove the identified tracks.
        """
        sp = get_client()
        playlist_id = playlist_id.split(":")[-1] if ":" in playlist_id else playlist_id

        try:
            playlist_info = sp.playlist(playlist_id, fields="name")
            playlist_name = playlist_info.get("name", "Unknown")
        except Exception as e:
            return f"**Error:** Could not fetch playlist: {e}"

        all_items = fetch_all_playlist_items(sp, playlist_id)

        unavailable = []
        duplicates = []
        seen_uris = {}

        for i, item in enumerate(all_items):
            track = item.get("track")

            # Check for unavailable tracks
            if remove_unavailable:
                if track is None or track.get("is_playable") == False:
                    unavailable.append({
                        "position": i,
                        "name": track.get("name", "Unknown") if track else "Unknown",
                        "artist": (track.get("artists", [{}])[0].get("name", "Unknown")
                                   if track else "Unknown"),
                        "uri": track.get("uri") if track else None,
                    })
                    continue  # Don't also flag as duplicate

            # Check for duplicates
            if track and track.get("uri"):
                uri = track["uri"]
                if uri in seen_uris:
                    if remove_duplicates:
                        duplicates.append({
                            "position": i,
                            "name": track.get("name", "Unknown"),
                            "artist": track.get("artists", [{}])[0].get("name", "Unknown"),
                            "uri": uri,
                            "first_seen": seen_uris[uri],
                        })
                else:
                    seen_uris[uri] = i

        # Build report
        lines = [
            f"**Playlist Cleanup Report** for \"{playlist_name}\"",
            f"Total tracks scanned: {len(all_items)}",
            "",
        ]

        if not unavailable and not duplicates:
            lines.append("Playlist is clean — no issues found.")
            return "\n".join(lines)

        if unavailable:
            lines.append(f"### Unavailable Tracks: {len(unavailable)}")
            for j, t in enumerate(unavailable[:20], 1):
                lines.append(f"{j}. **{t['name']}** by {t['artist']} (position {t['position']})")
            if len(unavailable) > 20:
                lines.append(f"_...and {len(unavailable) - 20} more_")
            lines.append("")

        if duplicates:
            lines.append(f"### Duplicate Tracks: {len(duplicates)}")
            for j, d in enumerate(duplicates[:20], 1):
                lines.append(
                    f"{j}. **{d['name']}** by {d['artist']} "
                    f"(position {d['position']}, first at {d['first_seen']})"
                )
            if len(duplicates) > 20:
                lines.append(f"_...and {len(duplicates) - 20} more_")
            lines.append("")

        if dry_run:
            total_issues = len(unavailable) + len(duplicates)
            lines.append(
                f"_Dry run — no changes made. Found {total_issues} issue(s). "
                f"Call again with `dry_run=False` to remove them._"
            )
        else:
            # Collect URIs to remove
            uris_to_remove = []
            for t in unavailable:
                if t.get("uri"):
                    uris_to_remove.append(t["uri"])
            for d in duplicates:
                uris_to_remove.append(d["uri"])

            # Deduplicate URIs for the removal call
            unique_uris = list(set(uris_to_remove))

            if unique_uris:
                for batch in chunked(unique_uris, 100):
                    sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)

                # If we removed all occurrences of duplicates, re-add the first occurrence
                # for tracks that were duplicated (not unavailable)
                if duplicates:
                    dup_uris_to_readd = []
                    unavailable_uris = set(t.get("uri") for t in unavailable if t.get("uri"))
                    for uri in set(d["uri"] for d in duplicates):
                        if uri not in unavailable_uris:
                            dup_uris_to_readd.append(uri)

                    if dup_uris_to_readd:
                        for batch in chunked(dup_uris_to_readd, 100):
                            sp.playlist_add_items(playlist_id, batch)

                removed_count = len(unavailable) + len(duplicates)
                lines.append(f"Removed {removed_count} track(s) from the playlist.")
            else:
                lines.append("No removable tracks found (unavailable tracks had no URI).")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_interleave_playlists(
        playlist_ids: list[str],
        name: str,
    ) -> str:
        """Create a new playlist by interleaving tracks from multiple playlists.

        Takes 2-5 playlists and creates a new one by round-robin picking one
        track from each source playlist in rotation. Duplicates across playlists
        are removed (first occurrence kept).

        Args:
            playlist_ids: List of 2-5 Spotify playlist IDs or URIs.
            name: Name for the new interleaved playlist.
        """
        if len(playlist_ids) < 2 or len(playlist_ids) > 5:
            return "**Error:** Provide between 2 and 5 playlist IDs."

        sp = get_client()
        user_id = sp.me()["id"]

        # Normalize IDs
        playlist_ids = [
            pid.split(":")[-1] if ":" in pid else pid
            for pid in playlist_ids
        ]

        # Fetch tracks from each playlist
        source_tracks = []
        source_names = []
        for pid in playlist_ids:
            try:
                playlist_info = sp.playlist(pid, fields="name")
                source_names.append(playlist_info.get("name", pid))
            except Exception as e:
                return f"**Error:** Could not fetch playlist `{pid}`: {e}"

            items = fetch_all_playlist_items(sp, pid)
            tracks = []
            for item in items:
                track = item.get("track")
                if track and track.get("uri"):
                    tracks.append(track["uri"])
            source_tracks.append(tracks)

        # Round-robin interleave
        interleaved = []
        max_len = max(len(t) for t in source_tracks)
        for i in range(max_len):
            for tracks in source_tracks:
                if i < len(tracks):
                    interleaved.append(tracks[i])

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for uri in interleaved:
            if uri not in seen:
                seen.add(uri)
                deduped.append(uri)

        if not deduped:
            return "**Error:** No tracks found across the provided playlists."

        # Create new playlist
        description = f"Interleaved from: {', '.join(source_names)}"
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=name,
            public=False,
            description=description,
        )
        new_id = new_playlist["id"]
        url = new_playlist.get("external_urls", {}).get("spotify", "")

        # Add tracks in batches of 100
        for batch in chunked(deduped, 100):
            sp.playlist_add_items(new_id, batch)

        lines = [
            f"**Interleaved Playlist Created:** {name}",
            f"ID: `{new_id}`",
            f"URL: {url}",
            f"Total tracks: {len(deduped)}",
            f"Sources: {', '.join(source_names)}",
        ]
        dupes_removed = len(interleaved) - len(deduped)
        if dupes_removed > 0:
            lines.append(f"Duplicates removed: {dupes_removed}")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_playlist_radio(
        playlist_id: str,
        name: str = None,
        track_count: int = 30,
    ) -> str:
        """Generate a radio-style playlist based on an existing playlist's artists.

        Analyzes the source playlist to find the most frequent artists, discovers
        their related artists, and builds a new playlist from those related artists'
        catalogs — excluding any tracks already in the source playlist.

        Args:
            playlist_id: Spotify playlist ID or URI of the source playlist.
            name: Name for the new radio playlist. Defaults to "{source_name} Radio".
            track_count: Number of tracks for the radio playlist (1-50, default 30).
        """
        track_count = max(1, min(50, track_count))

        sp = get_client()
        playlist_id = playlist_id.split(":")[-1] if ":" in playlist_id else playlist_id
        user_id = sp.me()["id"]

        try:
            playlist_info = sp.playlist(playlist_id, fields="name")
            playlist_name = playlist_info.get("name", "Unknown")
        except Exception as e:
            return f"**Error:** Could not fetch playlist: {e}"

        all_items = fetch_all_playlist_items(sp, playlist_id)

        if not all_items:
            return "**Error:** Source playlist is empty."

        # Extract artist frequencies and existing track URIs
        artist_counts = {}
        existing_uris = set()
        for item in all_items:
            track = item.get("track")
            if not track or not track.get("uri"):
                continue
            existing_uris.add(track["uri"])
            for artist in track.get("artists", []):
                aid = artist.get("id")
                if aid:
                    artist_counts[aid] = artist_counts.get(aid, 0) + 1

        if not artist_counts:
            return "**Error:** No artist data found in playlist tracks."

        # Get top 5 most frequent artists
        top_artists = sorted(artist_counts.keys(), key=lambda a: artist_counts[a], reverse=True)[:5]

        # Discover related artists and collect candidate tracks
        candidate_uris = []
        related_artist_ids = set()

        for artist_id in top_artists:
            try:
                related = sp.artist_related_artists(artist_id)
                related_artists = related.get("artists", [])
            except Exception:
                logger.warning("Failed to fetch related artists for %s", artist_id)
                continue

            if not related_artists:
                continue

            # Sample up to 3 related artists per seed artist
            sampled = random.sample(related_artists, min(3, len(related_artists)))

            for ra in sampled:
                ra_id = ra.get("id")
                if not ra_id or ra_id in related_artist_ids:
                    continue
                related_artist_ids.add(ra_id)

                # Fetch albums for this related artist
                try:
                    albums = fetch_artist_albums(sp, ra_id, include_groups="album,single")
                except Exception:
                    logger.warning("Failed to fetch albums for related artist %s", ra_id)
                    continue

                if not albums:
                    continue

                # Sample up to 2 albums to keep API calls reasonable
                sampled_albums = random.sample(albums, min(2, len(albums)))

                for album in sampled_albums:
                    album_id = album.get("id")
                    if not album_id:
                        continue
                    try:
                        album_tracks = sp.album_tracks(album_id, limit=50)
                        for t in album_tracks.get("items", []):
                            uri = t.get("uri")
                            if uri and uri not in existing_uris:
                                candidate_uris.append(uri)
                    except Exception:
                        logger.warning("Failed to fetch tracks for album %s", album_id)
                        continue

        if not candidate_uris:
            return "**Error:** Could not find any new tracks from related artists."

        # Deduplicate candidates, shuffle, and take desired count
        unique_candidates = list(set(candidate_uris))
        random.shuffle(unique_candidates)
        selected = unique_candidates[:track_count]

        # Create the radio playlist
        radio_name = name if name else f"{playlist_name} Radio"
        description = f"Radio inspired by \"{playlist_name}\""

        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=radio_name,
            public=False,
            description=description,
        )
        new_id = new_playlist["id"]
        url = new_playlist.get("external_urls", {}).get("spotify", "")

        # Add tracks in batches of 100
        for batch in chunked(selected, 100):
            sp.playlist_add_items(new_id, batch)

        lines = [
            f"**Playlist Radio Created:** {radio_name}",
            f"ID: `{new_id}`",
            f"URL: {url}",
            f"Tracks: {len(selected)}",
            f"Based on: \"{playlist_name}\" ({len(all_items)} tracks)",
            f"Sourced from {len(related_artist_ids)} related artists",
        ]

        return "\n".join(lines)
