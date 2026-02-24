"""Queue building tools — 2 tools."""

import logging
import time
import random
from spotipy.exceptions import SpotifyException
from ..utils.spotify_client import get_client
from ..utils.pagination import fetch_all_playlist_items

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    def spotify_build_queue(uris: list[str]) -> str:
        """Add multiple tracks to the playback queue in order.

        Args:
            uris: List of Spotify track URIs to queue. Max 50.

        Requires an active Spotify device.
        """
        if not uris:
            return "**Error:** No URIs provided."
        if len(uris) > 50:
            return "**Error:** Max 50 tracks per call."

        sp = get_client()
        added = 0
        failed = 0
        for uri in uris:
            try:
                sp.add_to_queue(uri)
                added += 1
                time.sleep(0.1)  # Brief delay to avoid rate limits
            except SpotifyException as e:
                if e.http_status == 404:
                    return (
                        f"**Error:** No active device found. "
                        f"Open Spotify on a device first. "
                        f"(Added {added} tracks before failure.)"
                    )
                failed += 1
                logger.warning(f"Failed to queue {uri}: {e}")

        lines = [f"**Queue Built:** Added {added} track(s) to queue."]
        if failed:
            lines.append(f"_{failed} track(s) failed to add._")
        return "\n".join(lines)

    @mcp.tool()
    def spotify_queue_from_playlist(
        playlist_id: str,
        count: int = 10,
        shuffle: bool = True,
    ) -> str:
        """Queue tracks from a playlist.

        Args:
            playlist_id: Spotify playlist ID.
            count: Number of tracks to queue (1-50). Default 10.
            shuffle: If True, randomly select tracks. If False, take from the start.

        Requires an active Spotify device.
        """
        count = max(1, min(50, count))
        sp = get_client()

        items = fetch_all_playlist_items(sp, playlist_id)
        if not items:
            return "**Error:** Playlist is empty."

        # Extract valid tracks
        tracks = []
        for item in items:
            track = item.get("track")
            if track and track.get("uri"):
                tracks.append(track)

        if not tracks:
            return "**Error:** No playable tracks in playlist."

        # Select tracks
        if shuffle:
            selected = random.sample(tracks, min(count, len(tracks)))
        else:
            selected = tracks[:count]

        # Queue them
        added = 0
        for track in selected:
            try:
                sp.add_to_queue(track["uri"])
                added += 1
                time.sleep(0.1)
            except SpotifyException as e:
                if e.http_status == 404:
                    return (
                        f"**Error:** No active device found. "
                        f"(Added {added} tracks before failure.)"
                    )
                logger.warning(f"Failed to queue {track.get('name', '?')}: {e}")

        return f"**Queued {added} track(s)** from playlist."
