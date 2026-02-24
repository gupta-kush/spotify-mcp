"""Podcast and show tools — 8 tools."""

import logging
from ..utils.spotify_client import get_client
from ..utils.formatting import format_show, format_episode, ms_to_duration
from ..utils.uri_parser import parse_spotify_id

logger = logging.getLogger(__name__)


def register(mcp):

    @mcp.tool()
    def spotify_get_saved_shows(limit: int = 20) -> str:
        """Get your saved/followed podcasts and shows.

        Args:
            limit: Number of shows to return (1-50). Default 20.
        """
        limit = max(1, min(50, limit))
        sp = get_client()
        results = sp.current_user_saved_shows(limit=limit)
        items = results.get("items", [])
        total = results.get("total", 0)

        if not items:
            return "You have no saved shows."

        header = f"**Saved Shows** ({total} total):\n\n"
        lines = [header]
        for i, item in enumerate(items, 1):
            show = item.get("show")
            if show:
                lines.append(f"{i}. {format_show(show)}")
        return "\n".join(lines)

    @mcp.tool()
    def spotify_get_show(show_id: str) -> str:
        """Get detailed information about a podcast or show.

        Args:
            show_id: Spotify show ID or URI.
        """
        sp = get_client()
        show_id = parse_spotify_id(show_id)
        show = sp.show(show_id)

        lines = [
            f"# {show.get('name', 'Unknown')}",
            "",
            f"**Publisher:** {show.get('publisher', 'Unknown')}",
            f"**Total Episodes:** {show.get('total_episodes', '?')}",
            f"**Languages:** {', '.join(show.get('languages', []))}",
            f"**Explicit:** {'Yes' if show.get('explicit') else 'No'}",
            "",
        ]
        desc = show.get("description", "")
        if desc:
            lines.append(f"_{desc[:300]}_")
            lines.append("")

        lines.append(f"ID: `{show.get('id', '')}`")
        url = show.get("external_urls", {}).get("spotify", "")
        if url:
            lines.append(f"URL: {url}")

        return "\n".join(lines)

    @mcp.tool()
    def spotify_get_show_episodes(show_id: str, limit: int = 20) -> str:
        """Get episodes of a podcast or show (newest first).

        Args:
            show_id: Spotify show ID or URI.
            limit: Number of episodes to return (1-50). Default 20.
        """
        limit = max(1, min(50, limit))
        sp = get_client()
        show_id = parse_spotify_id(show_id)
        results = sp.show_episodes(show_id, limit=limit)
        items = results.get("items", [])
        total = results.get("total", 0)

        if not items:
            return "No episodes found."

        header = f"**Episodes** ({total} total, showing {len(items)}):\n\n"
        lines = [header]
        for i, ep in enumerate(items, 1):
            lines.append(f"{i}. {format_episode(ep)}")
        return "\n".join(lines)

    @mcp.tool()
    def spotify_save_shows(show_ids: list[str]) -> str:
        """Save podcasts/shows to your library.

        Args:
            show_ids: List of Spotify show IDs or URIs. Max 50 per call.
        """
        if not show_ids:
            return "**Error:** No show IDs provided."
        if len(show_ids) > 50:
            return "**Error:** Max 50 shows per call."
        sp = get_client()
        ids = [parse_spotify_id(s) for s in show_ids]
        sp.current_user_saved_shows_add(ids)
        return f"Saved {len(ids)} show(s) to your library."

    @mcp.tool()
    def spotify_remove_saved_shows(show_ids: list[str]) -> str:
        """Remove podcasts/shows from your library.

        Args:
            show_ids: List of Spotify show IDs or URIs. Max 50 per call.
        """
        if not show_ids:
            return "**Error:** No show IDs provided."
        if len(show_ids) > 50:
            return "**Error:** Max 50 shows per call."
        sp = get_client()
        ids = [parse_spotify_id(s) for s in show_ids]
        sp.current_user_saved_shows_delete(ids)
        return f"Removed {len(ids)} show(s) from your library."

    @mcp.tool()
    def spotify_check_saved_shows(show_ids: list[str]) -> str:
        """Check which shows are saved in your library.

        Args:
            show_ids: List of Spotify show IDs or URIs to check. Max 50 per call.
        """
        if not show_ids:
            return "**Error:** No show IDs provided."
        if len(show_ids) > 50:
            return "**Error:** Max 50 shows per call."
        sp = get_client()
        ids = [parse_spotify_id(s) for s in show_ids]
        results = sp.current_user_saved_shows_contains(ids)
        lines = ["**Saved Show Check:**", ""]
        for sid, saved in zip(ids, results):
            status = "Saved" if saved else "Not saved"
            lines.append(f"- `{sid}`: {status}")
        return "\n".join(lines)

    @mcp.tool()
    def spotify_save_episodes(episode_ids: list[str]) -> str:
        """Save podcast episodes to your library.

        Args:
            episode_ids: List of Spotify episode IDs or URIs. Max 50 per call.
        """
        if not episode_ids:
            return "**Error:** No episode IDs provided."
        if len(episode_ids) > 50:
            return "**Error:** Max 50 episodes per call."
        sp = get_client()
        ids = [parse_spotify_id(e) for e in episode_ids]
        sp.current_user_saved_episodes_add(ids)
        return f"Saved {len(ids)} episode(s) to your library."

    @mcp.tool()
    def spotify_get_episode(episode_id: str) -> str:
        """Get detailed information about a podcast episode.

        Args:
            episode_id: Spotify episode ID or URI.
        """
        sp = get_client()
        episode_id = parse_spotify_id(episode_id)
        ep = sp.episode(episode_id)

        lines = [
            f"# {ep.get('name', 'Unknown')}",
            "",
            f"**Show:** {ep.get('show', {}).get('name', 'Unknown')}",
            f"**Release Date:** {ep.get('release_date', '?')}",
            f"**Duration:** {ms_to_duration(ep.get('duration_ms', 0))}",
            f"**Explicit:** {'Yes' if ep.get('explicit') else 'No'}",
            "",
        ]
        desc = ep.get("description", "")
        if desc:
            lines.append(f"_{desc[:500]}_")
            lines.append("")

        resume = ep.get("resume_point", {})
        if resume and resume.get("fully_played") is not None:
            if resume.get("fully_played"):
                lines.append("**Status:** Fully played")
            elif resume.get("resume_position_ms", 0) > 0:
                lines.append(f"**Resume at:** {ms_to_duration(resume['resume_position_ms'])}")

        lines.append(f"ID: `{ep.get('id', '')}`")
        url = ep.get("external_urls", {}).get("spotify", "")
        if url:
            lines.append(f"URL: {url}")

        return "\n".join(lines)
