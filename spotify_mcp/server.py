import importlib
import os
import sys
import logging
from mcp.server.fastmcp import FastMCP
from spotipy.exceptions import SpotifyException

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
    """Check Spotify connection status, profile info, and current playback."""
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
    except SpotifyException as e:
        lines.append(f"**Playback:** Could not fetch ({e})")

    return "\n".join(lines)


# --- Module registry and toolset loading ---

# Module registry — maps module name to (package, import_name)
_MODULE_REGISTRY = {
    # tools/ modules
    "playback": ("tools", "playback"),
    "playlists": ("tools", "playlists"),
    "search": ("tools", "search"),
    "discovery": ("tools", "discovery"),
    "stats": ("tools", "stats"),
    "library": ("tools", "library"),
    "follow": ("tools", "follow"),
    "shows": ("tools", "shows"),
    "browse": ("tools", "browse"),
    # power/ modules
    "playlist_ops": ("power", "playlist_ops"),
    "reports": ("power", "reports"),
    "smart_shuffle": ("power", "smart_shuffle"),
    "deep_dive": ("power", "deep_dive"),
    "playlist_generator": ("power", "playlist_generator"),
    "playlist_sort": ("power", "playlist_sort"),
    "playlist_curator": ("power", "playlist_curator"),
    "queue_builder": ("power", "queue_builder"),
    "vibe_engine": ("power", "vibe_engine"),
    "insights": ("power", "insights"),
    "artist_explorer": ("power", "artist_explorer"),
    "find_song": ("power", "find_song"),
}


def _parse_toolsets() -> str:
    """Get toolsets from CLI args or env var.

    Priority: --toolsets CLI flag > SPOTIFY_MCP_TOOLSETS env var > "all"
    """
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--toolsets="):
            return arg.split("=", 1)[1]
        if arg == "--toolsets" and i < len(sys.argv) - 1:
            return sys.argv[i + 1]
    return os.environ.get("SPOTIFY_MCP_TOOLSETS", "all")


def _resolve_toolsets(toolset_str: str) -> list[str]:
    """Resolve toolset names to a list of module names."""
    from .config import TOOLSET_MODULES

    if toolset_str == "all":
        return list(_MODULE_REGISTRY.keys())

    modules = []
    for name in toolset_str.split(","):
        name = name.strip()
        if name == "all":
            return list(_MODULE_REGISTRY.keys())
        elif name in TOOLSET_MODULES:
            modules.extend(TOOLSET_MODULES[name])
        elif name in _MODULE_REGISTRY:
            # Allow individual module names too
            modules.append(name)
        else:
            logger.warning(f"Unknown toolset or module: {name}")

    return list(dict.fromkeys(modules))  # dedupe preserving order


def _register_modules(module_names: list[str]):
    """Import and register the specified tool modules."""
    for name in module_names:
        if name not in _MODULE_REGISTRY:
            logger.warning(f"Unknown module: {name}")
            continue
        package, module = _MODULE_REGISTRY[name]
        try:
            mod = importlib.import_module(f".{package}.{module}", package="spotify_mcp")
            mod.register(mcp)
        except Exception as e:
            logger.error(f"Failed to register module {name}: {e}")

    logger.info(f"Registered {len(module_names)} tool modules: {', '.join(module_names)}")


# --- Perform registration at import time ---

_toolsets = _parse_toolsets()
_register_modules(_resolve_toolsets(_toolsets))

from .config import SPOTIFY_CLIENT_ID
if not SPOTIFY_CLIENT_ID:
    logger.warning(
        "SPOTIFY_CLIENT_ID not set. "
        "Copy .env.example to .env and add your credentials. "
        "See: https://developer.spotify.com/dashboard"
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
