import sys
import logging
from mcp.server.fastmcp import FastMCP

# Logging to stderr — critical for stdio transport (stdout is the MCP channel)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="Spotify",
)


# --- Smoke-test tool (Phase 1) ---

@mcp.tool()
def spotify_status() -> str:
    """Get your Spotify connection status, profile info, and current playback state.

    Use this to verify the Spotify MCP is working correctly.
    """
    from .utils.spotify_client import get_client
    from .utils.formatting import format_track, format_device

    sp = get_client()

    # User profile
    me = sp.me()
    name = me.get("display_name", "Unknown")
    user_id = me.get("id", "")

    lines = [
        f"**Connected as:** {name} (`{user_id}`)",
        "",
    ]

    # Current playback
    try:
        playback = sp.current_playback()
        if playback and playback.get("item"):
            track = playback["item"]
            device = playback.get("device", {})
            is_playing = playback.get("is_playing", False)
            status = "Playing" if is_playing else "Paused"

            lines.append(f"**Playback:** {status}")
            lines.append(format_track(track))
            if device:
                lines.append(format_device(device))
        else:
            lines.append("**Playback:** Nothing currently playing")
    except Exception as e:
        lines.append(f"**Playback:** Could not fetch ({e})")

    return "\n".join(lines)


# --- Register tool modules ---

def _register_all():
    """Import and register all tool modules."""
    from .tools.playback import register as register_playback
    from .tools.playlists import register as register_playlists
    from .tools.search import register as register_search
    from .tools.discovery import register as register_discovery
    from .tools.stats import register as register_stats
    from .tools.library import register as register_library
    from .power.playlist_ops import register as register_playlist_ops
    from .power.reports import register as register_reports
    from .power.smart_shuffle import register as register_smart_shuffle
    from .power.deep_dive import register as register_deep_dive
    from .tools.follow import register as register_follow
    from .tools.shows import register as register_shows
    from .power.playlist_generator import register as register_playlist_generator
    from .power.playlist_sort import register as register_playlist_sort
    from .power.playlist_curator import register as register_playlist_curator
    from .power.queue_builder import register as register_queue_builder
    from .power.vibe_engine import register as register_vibe_engine
    from .power.insights import register as register_insights
    from .power.artist_explorer import register as register_artist_explorer
    from .power.find_song import register as register_find_song
    from .tools.browse import register as register_browse

    register_playback(mcp)
    register_playlists(mcp)
    register_search(mcp)
    register_discovery(mcp)
    register_stats(mcp)
    register_library(mcp)
    register_follow(mcp)
    register_shows(mcp)
    register_playlist_ops(mcp)
    register_reports(mcp)
    register_smart_shuffle(mcp)
    register_deep_dive(mcp)
    register_playlist_generator(mcp)
    register_playlist_sort(mcp)
    register_playlist_curator(mcp)
    register_queue_builder(mcp)
    register_vibe_engine(mcp)
    register_insights(mcp)
    register_artist_explorer(mcp)
    register_find_song(mcp)
    register_browse(mcp)

    logger.info("All tool modules registered")


_register_all()

from .config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    logger.warning(
        "SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set. "
        "Copy .env.example to .env and add your credentials. "
        "See: https://developer.spotify.com/dashboard"
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
