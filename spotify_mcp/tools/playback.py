"""Playback control tools — 14 tools for player management."""

import logging
from spotipy.exceptions import SpotifyException
from ..utils.spotify_client import get_client
from ..utils.errors import catch_spotify_errors
from ..utils.formatting import format_track, format_device, ms_to_duration

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    @catch_spotify_errors
    def spotify_now_playing() -> str:
        """Get the currently playing track, playback state, and device info.

        Returns track name, artist, album, progress, and which device is active.
        """
        sp = get_client()
        playback = sp.current_playback()
        if not playback or not playback.get("item"):
            return "Nothing is currently playing."

        track = playback["item"]
        device = playback.get("device", {})
        is_playing = playback.get("is_playing", False)
        progress = playback.get("progress_ms", 0)
        duration = track.get("duration_ms", 0)
        shuffle = playback.get("shuffle_state", False)
        repeat = playback.get("repeat_state", "off")

        lines = [
            f"**{'Playing' if is_playing else 'Paused'}**",
            format_track(track),
            f"Progress: {ms_to_duration(progress)} / {ms_to_duration(duration)}",
            f"Shuffle: {'On' if shuffle else 'Off'} | Repeat: {repeat}",
        ]
        if device:
            lines.append(format_device(device))
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_play(
        uri: str = None,
        context_uri: str = None,
        device_id: str = None,
        offset: int = None,
    ) -> str:
        """Start playback of a track, album, or playlist.

        Args:
            uri: Spotify URI of a specific track (e.g., spotify:track:xxx). Plays this track.
            context_uri: Spotify URI of an album or playlist to play (e.g., spotify:album:xxx).
            device_id: Target device ID. If omitted, uses the active device.
            offset: Position in the context to start from (0-indexed). Only used with context_uri.
        """
        sp = get_client()
        kwargs = {}
        if device_id:
            kwargs["device_id"] = device_id

        if uri:
            kwargs["uris"] = [uri]
        elif context_uri:
            kwargs["context_uri"] = context_uri
            if offset is not None:
                kwargs["offset"] = {"position": offset}
        else:
            # Resume playback
            sp.start_playback(**kwargs)
            return "Playback resumed."

        sp.start_playback(**kwargs)
        return f"Now playing: {uri or context_uri}"

    @mcp.tool()
    @catch_spotify_errors
    def spotify_pause(device_id: str = None) -> str:
        """Pause the current playback.

        Args:
            device_id: Target device ID. If omitted, uses the active device.
        """
        sp = get_client()
        kwargs = {}
        if device_id:
            kwargs["device_id"] = device_id
        sp.pause_playback(**kwargs)
        return "Playback paused."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_resume(device_id: str = None) -> str:
        """Resume paused playback.

        Args:
            device_id: Target device ID. If omitted, uses the active device.
        """
        sp = get_client()
        kwargs = {}
        if device_id:
            kwargs["device_id"] = device_id
        sp.start_playback(**kwargs)
        return "Playback resumed."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_skip_next(device_id: str = None) -> str:
        """Skip to the next track.

        Args:
            device_id: Target device ID. If omitted, uses the active device.
        """
        sp = get_client()
        kwargs = {}
        if device_id:
            kwargs["device_id"] = device_id
        sp.next_track(**kwargs)
        return "Skipped to next track."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_skip_previous(device_id: str = None) -> str:
        """Skip to the previous track.

        Args:
            device_id: Target device ID. If omitted, uses the active device.
        """
        sp = get_client()
        kwargs = {}
        if device_id:
            kwargs["device_id"] = device_id
        sp.previous_track(**kwargs)
        return "Skipped to previous track."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_add_to_queue(uri: str) -> str:
        """Add a track or episode to the playback queue.

        Args:
            uri: Spotify URI of the track or episode (e.g., spotify:track:xxx).
        """
        sp = get_client()
        sp.add_to_queue(uri)
        return f"Added to queue: {uri}"

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_queue() -> str:
        """Get the current playback queue.

        Returns the currently playing track and upcoming tracks in the queue.
        """
        sp = get_client()
        queue = sp.queue()
        lines = []

        current = queue.get("currently_playing")
        if current:
            lines.append("**Now playing:**")
            lines.append(format_track(current))
            lines.append("")

        upcoming = queue.get("queue", [])
        if upcoming:
            lines.append(f"**Queue ({len(upcoming)} tracks):**")
            for i, track in enumerate(upcoming[:20], 1):
                lines.append(format_track(track, index=i))
            if len(upcoming) > 20:
                lines.append(f"\n_...and {len(upcoming) - 20} more_")
        else:
            lines.append("Queue is empty.")

        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_get_devices() -> str:
        """List all available Spotify Connect devices.

        Shows device name, type, active status, and volume level.
        """
        sp = get_client()
        devices = sp.devices().get("devices", [])
        if not devices:
            return "No devices found. Make sure Spotify is open on at least one device."

        lines = ["**Available Devices:**"]
        for d in devices:
            lines.append(format_device(d))
        return "\n".join(lines)

    @mcp.tool()
    @catch_spotify_errors
    def spotify_set_volume(volume_percent: int, device_id: str = None) -> str:
        """Set the playback volume.

        Args:
            volume_percent: Volume level from 0 to 100.
            device_id: Target device ID. If omitted, uses the active device.

        Requires Spotify Premium.
        """
        if not 0 <= volume_percent <= 100:
            return "**Error:** Volume must be between 0 and 100."
        sp = get_client()
        kwargs = {"volume_percent": volume_percent}
        if device_id:
            kwargs["device_id"] = device_id
        sp.volume(**kwargs)
        return f"Volume set to {volume_percent}%."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_seek(position_ms: int) -> str:
        """Seek to a position in the currently playing track.

        Args:
            position_ms: Position in milliseconds to seek to.

        Requires Spotify Premium.
        """
        sp = get_client()
        sp.seek_track(position_ms)
        return f"Seeked to {ms_to_duration(position_ms)}."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_set_repeat(state: str) -> str:
        """Set the repeat mode for playback.

        Args:
            state: Repeat mode — "off" (no repeat), "context" (repeat playlist/album),
                   or "track" (repeat current track).

        Requires Spotify Premium.
        """
        if state not in ("off", "context", "track"):
            return "**Error:** State must be one of: off, context, track."
        sp = get_client()
        sp.repeat(state)
        return f"Repeat mode set to {state}."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_toggle_shuffle(state: bool) -> str:
        """Turn shuffle on or off.

        Args:
            state: True to enable shuffle, False to disable.

        Requires Spotify Premium.
        """
        sp = get_client()
        sp.shuffle(state)
        return f"Shuffle {'on' if state else 'off'}."

    @mcp.tool()
    @catch_spotify_errors
    def spotify_transfer_playback(device_id: str, force_play: bool = False) -> str:
        """Transfer playback to a different device.

        Args:
            device_id: Target device ID (get IDs from spotify_get_devices).
            force_play: If True, start playing on new device. If False, keep current state.

        Requires Spotify Premium.
        """
        sp = get_client()
        sp.transfer_playback(device_id, force_play=force_play)
        return f"Playback transferred to device {device_id}."
