"""Markdown response formatters for Claude."""

from ..config import MAX_DISPLAY_ITEMS


def format_track(track: dict, index: int = None) -> str:
    """Format a single track as a markdown line."""
    if not track:
        return "_Unknown track_"
    name = track.get("name", "Unknown")
    artists = ", ".join(a["name"] for a in track.get("artists", []))
    album = track.get("album", {}).get("name", "")
    duration_ms = track.get("duration_ms", 0)
    minutes = duration_ms // 60000
    seconds = (duration_ms % 60000) // 1000

    prefix = f"{index}. " if index is not None else "- "
    line = f"{prefix}**{name}** by {artists}"
    if album:
        line += f" ({album})"
    line += f" [{minutes}:{seconds:02d}]"
    return line


def format_track_list(tracks: list, numbered: bool = True) -> str:
    """Format a list of tracks as markdown."""
    if not tracks:
        return "_No tracks found._"

    total = len(tracks)
    display = tracks[:MAX_DISPLAY_ITEMS]
    lines = []
    for i, t in enumerate(display, 1):
        # Handle both raw track objects and playlist item wrappers
        track = t.get("track", t) if isinstance(t, dict) else t
        idx = i if numbered else None
        lines.append(format_track(track, index=idx))

    result = "\n".join(lines)
    if total > MAX_DISPLAY_ITEMS:
        result += f"\n\n_Showing {MAX_DISPLAY_ITEMS} of {total} tracks._"
    return result


def format_artist(artist: dict, index: int = None) -> str:
    """Format a single artist as a markdown line."""
    if not artist:
        return "_Unknown artist_"
    name = artist.get("name", "Unknown")
    genres = ", ".join(artist.get("genres", [])[:3])
    prefix = f"{index}. " if index is not None else "- "
    line = f"{prefix}**{name}**"
    if genres:
        line += f" ({genres})"
    return line


def format_artist_list(artists: list, numbered: bool = True) -> str:
    """Format a list of artists as markdown."""
    if not artists:
        return "_No artists found._"

    total = len(artists)
    display = artists[:MAX_DISPLAY_ITEMS]
    lines = []
    for i, a in enumerate(display, 1):
        idx = i if numbered else None
        lines.append(format_artist(a, index=idx))

    result = "\n".join(lines)
    if total > MAX_DISPLAY_ITEMS:
        result += f"\n\n_Showing {MAX_DISPLAY_ITEMS} of {total} artists._"
    return result


def format_playlist_summary(playlist: dict) -> str:
    """Format a playlist summary as markdown."""
    name = playlist.get("name", "Unknown")
    owner = playlist.get("owner", {}).get("display_name", "Unknown")
    total = playlist.get("tracks", {}).get("total", 0)
    public = "Public" if playlist.get("public") else "Private"
    desc = playlist.get("description", "")
    pid = playlist.get("id", "")

    lines = [
        f"**{name}** ({public})",
        f"  Owner: {owner} | {total} tracks | ID: `{pid}`",
    ]
    if desc:
        lines.append(f"  _{desc}_")
    return "\n".join(lines)


def format_playlist_list(playlists: list) -> str:
    """Format a list of playlists as markdown."""
    if not playlists:
        return "_No playlists found._"

    lines = []
    for i, p in enumerate(playlists[:MAX_DISPLAY_ITEMS], 1):
        name = p.get("name", "Unknown")
        total = p.get("tracks", {}).get("total", 0)
        public = "Public" if p.get("public") else "Private"
        lines.append(f"{i}. **{name}** — {total} tracks ({public}) | ID: `{p.get('id', '')}`")

    result = "\n".join(lines)
    if len(playlists) > MAX_DISPLAY_ITEMS:
        result += f"\n\n_Showing {MAX_DISPLAY_ITEMS} of {len(playlists)} playlists._"
    return result


def format_device(device: dict) -> str:
    """Format a device as a markdown line."""
    name = device.get("name", "Unknown")
    dtype = device.get("type", "Unknown")
    active = " (active)" if device.get("is_active") else ""
    volume = device.get("volume_percent", "?")
    return f"- **{name}** ({dtype}){active} — Volume: {volume}%"


def format_album(album: dict, index: int = None) -> str:
    """Format a single album as a markdown line."""
    if not album:
        return "_Unknown album_"
    name = album.get("name", "Unknown")
    artists = ", ".join(a["name"] for a in album.get("artists", []))
    release = album.get("release_date", "Unknown")
    total = album.get("total_tracks", "?")
    album_type = album.get("album_type", "album")
    prefix = f"{index}. " if index is not None else "- "
    return f"{prefix}**{name}** by {artists} ({release}, {album_type}, {total} tracks)"


def ms_to_duration(ms: int) -> str:
    """Convert milliseconds to human-readable duration."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {seconds}s"


def format_album_detail(album: dict) -> str:
    """Format a rich album display for saved-albums as markdown."""
    if not album:
        return "_Unknown album_"
    name = album.get("name", "Unknown")
    artists = ", ".join(a["name"] for a in album.get("artists", []))
    release_date = album.get("release_date", "Unknown")
    total_tracks = album.get("total_tracks", "?")
    label = album.get("label", "Unknown")
    url = album.get("external_urls", {}).get("spotify", "")
    album_id = album.get("id", "")

    lines = [
        f"**{name}**",
        f"  Artists: {artists}",
        f"  Released: {release_date}",
        f"  Tracks: {total_tracks}",
        f"  Label: {label}",
        f"  URL: {url}",
        f"  ID: `{album_id}`",
    ]
    return "\n".join(lines)


def format_show(show: dict) -> str:
    """Format a podcast show as markdown."""
    if not show:
        return "_Unknown show_"
    name = show.get("name", "Unknown")
    publisher = show.get("publisher", "Unknown")
    total_episodes = show.get("total_episodes", "?")
    description = show.get("description", "")
    if len(description) > 150:
        description = description[:150] + "..."
    show_id = show.get("id", "")

    lines = [
        f"**{name}**",
        f"  Publisher: {publisher}",
        f"  Episodes: {total_episodes}",
        f"  {description}",
        f"  ID: `{show_id}`",
    ]
    return "\n".join(lines)


def format_episode(episode: dict) -> str:
    """Format a podcast episode as markdown."""
    if not episode:
        return "_Unknown episode_"
    name = episode.get("name", "Unknown")
    duration_ms = episode.get("duration_ms", 0)
    duration = ms_to_duration(duration_ms)
    release_date = episode.get("release_date", "Unknown")
    description = episode.get("description", "")
    if len(description) > 120:
        description = description[:120] + "..."
    episode_id = episode.get("id", "")

    lines = [
        f"**{name}**",
        f"  Duration: {duration}",
        f"  Released: {release_date}",
        f"  {description}",
        f"  ID: `{episode_id}`",
    ]
    return "\n".join(lines)


def format_time_distribution(hour_counts: dict) -> str:
    """Format an ASCII bar chart of listening hours as markdown."""
    max_count = max(hour_counts.values()) if hour_counts else 0
    lines = []
    for hour in range(24):
        count = hour_counts.get(hour, 0)
        if max_count > 0:
            bar_len = int((count / max_count) * 20)
        else:
            bar_len = 0
        bar = "\u2588" * bar_len
        lines.append(f"{hour:02d}:00  {bar}  ({count})")
    return "\n".join(lines)


def format_genre_chart(genre_counts: dict, limit: int = 15) -> str:
    """Format a ranked genre bar chart as markdown."""
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_genres = sorted_genres[:limit]
    max_count = sorted_genres[0][1] if sorted_genres else 0
    lines = []
    for rank, (genre, count) in enumerate(sorted_genres, 1):
        if max_count > 0:
            bar_len = int((count / max_count) * 20)
        else:
            bar_len = 0
        bar = "\u2588" * bar_len
        lines.append(f"{rank}. {genre}  {bar}  ({count})")
    return "\n".join(lines)
