<!-- mcp-name: io.github.gupta-kush/spotify-mcp -->
# Spotify MCP Server

[![PyPI](https://img.shields.io/pypi/v/spotify-mcp)](https://pypi.org/project/spotify-mcp/)
[![Tests](https://github.com/gupta-kush/spotify-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/gupta-kush/spotify-mcp/actions/workflows/test.yml)
![96 Tools](https://img.shields.io/badge/tools-96-brightgreen)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Control Spotify from Claude, Cursor, or any MCP client. **96 tools** -- not just play/pause, but smart shuffling, vibe analysis, natural language song search, artist network mapping, taste evolution tracking, and way more. Built for Spotify's [post-February 2026 API](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security) where most other servers broke.

<!-- TODO: Replace with actual demo GIF -->

## Why this one?

There are 30+ Spotify MCP servers out there. Most give you 10-15 tools covering play, pause, search, done. This one goes deeper:

| | spotify-mcp | Typical server |
|---|---|---|
| **Tools** | **96** | 5-15 |
| **Smart shuffle** (6 strategies including energy arcs) | Yes | No |
| **Vibe engine** -- mood analysis without audio-features API | Yes | No |
| **"Find that sad piano song from the 2000s"** | Yes | No |
| **Map an artist's network** of 100 related artists | Yes | No |
| **"How has my taste changed?"** -- evolution tracking | Yes | No |
| **Library index** -- AI playlists from songs you already know | Yes | No |
| **Destructive tools stripped by default** -- safe for auto-accept | Yes | No |
| **Merge / diff / deduplicate** playlists | Yes | No |
| **Works after Spotify's Feb 2026 API changes** | Yes | Most broke |
| **PKCE auth** -- no client secret needed | Yes | Rare |

## Quick Start

### 1. Install

```bash
uvx spotify-mcp
```

Or with pip:

```bash
pip install spotify-mcp
```

### 2. Get Spotify Credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Set the **Redirect URI** to `http://127.0.0.1:8888/callback`
4. Check **Web API** and click **Save**
5. Copy your **Client ID** (Client Secret is optional -- PKCE auth works without it)

### 3. Configure Your Client

**Claude Desktop** -- add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": ["spotify-mcp"],
      "env": {
        "SPOTIFY_CLIENT_ID": "your_client_id"
      }
    }
  }
}
```

**Cursor / VS Code** -- use the same config, but load only core tools to stay under the 40-tool limit:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": ["spotify-mcp", "--toolsets=core"],
      "env": {
        "SPOTIFY_CLIENT_ID": "your_client_id"
      }
    }
  }
}
```

### 4. First Run

The first time you use a Spotify tool, your browser opens for OAuth authorization. Grant access and the token is cached locally.

## What can you do with it?

Just talk to your AI assistant like you'd talk to a friend who has access to your Spotify:

- "Play Bohemian Rhapsody"
- "Make my playlist start chill and build to high energy" -- smart shuffle reorders it with an energy arc
- "Find that sad song with strings by Pink Floyd from the 90s" -- natural language, not exact titles
- "How has my music taste changed over time?" -- compares your short/medium/long term listening
- "Map Radiohead's related artist network" -- explores up to 100 connected artists
- "Create a 90s era playlist"
- "Compare my Gym and Running playlists" -- side-by-side genre and artist breakdown
- "Clean up my old playlist" -- finds and removes unavailable tracks and duplicates
- "What's the vibe of my Summer playlist?" -- genre-based energy and mood analysis
- "Create a radio playlist based on Radiohead" -- samples related artists' catalogs
- "When do I listen to music the most?" -- hour-of-day and day-of-week patterns

## Toolsets

By default, all 96 tools are loaded (minus destructive tools -- see [Safety](#safety) below). For clients with tool limits (Cursor: 40 max), use `--toolsets` to load only what you need:

```bash
spotify-mcp --toolsets=core              # ~27 tools: playback, playlists, search, library, browse, stats
spotify-mcp --toolsets=core,discovery    # Add music discovery
spotify-mcp --toolsets=core,power        # Add power tools (smart shuffle, vibe engine, etc.)
spotify-mcp --toolsets=all               # All tools (default, destructive excluded)
spotify-mcp --toolsets=all,destructive   # All tools including remove/unfollow
```

Or via environment variable: `SPOTIFY_MCP_TOOLSETS=core,power`

Available toolsets: `core`, `social`, `discovery`, `power`, `destructive`, `all`

## Safety

**Destructive tools are stripped by default.** Tools that remove tracks, unfollow artists, or delete content are not loaded unless you explicitly opt in with `--toolsets=all,destructive`. This makes the server safe for auto-accept mode -- the AI literally cannot call tools that don't exist.

Affected tools: `spotify_remove_from_playlist`, `spotify_remove_saved_tracks`, `spotify_remove_saved_albums`, `spotify_remove_saved_shows`, `spotify_unfollow_playlist`, `spotify_unfollow_artists`, `spotify_unfollow_users`

Even when destructive tools are enabled, they default to `dry_run=True` -- showing a preview of what would happen without actually executing. The AI must explicitly pass `dry_run=False` to perform the action.

## Tool Reference

<details>
<summary><strong>Playback (15 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_status` | Connection status and current playback |
| `spotify_now_playing` | Currently playing track details |
| `spotify_play` | Start playback (track, album, or playlist) |
| `spotify_pause` | Pause playback |
| `spotify_resume` | Resume playback |
| `spotify_skip_next` | Skip to next track |
| `spotify_skip_previous` | Skip to previous track |
| `spotify_add_to_queue` | Add a track to the queue |
| `spotify_get_queue` | View the playback queue |
| `spotify_get_devices` | List available Spotify Connect devices |
| `spotify_set_volume` | Set volume (0-100) |
| `spotify_seek` | Seek to a position in the current track |
| `spotify_set_repeat` | Set repeat mode (off/context/track) |
| `spotify_toggle_shuffle` | Toggle shuffle on or off |
| `spotify_transfer_playback` | Transfer playback to another device |

</details>

<details>
<summary><strong>Playlists (12 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_get_my_playlists` | List your playlists |
| `spotify_get_playlist` | Get playlist details and tracks |
| `spotify_get_playlist_tracks` | Get playlist tracks with pagination |
| `spotify_create_playlist` | Create a new playlist |
| `spotify_add_to_playlist` | Add tracks to a playlist |
| `spotify_remove_from_playlist` | Remove tracks from a playlist |
| `spotify_reorder_playlist` | Move tracks within a playlist |
| `spotify_update_playlist` | Update name, description, or visibility |
| `spotify_follow_playlist` | Follow a playlist |
| `spotify_unfollow_playlist` | Unfollow a playlist |
| `spotify_get_playlist_cover` | Get the playlist's cover image URL |
| `spotify_check_playlist_followers` | Check if users follow a playlist |

</details>

<details>
<summary><strong>Search & Discovery (6 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_search` | Search for tracks, artists, albums, or playlists |
| `spotify_related_artists` | Find artists similar to a given artist |
| `spotify_discover_by_artist` | Discover tracks via related artists |
| `spotify_discover_by_mood` | Find tracks matching a mood |
| `spotify_genre_explorer` | Explore tracks and artists in a genre |
| `spotify_discover_deep_cuts` | Find album-only tracks (not singles) |

</details>

<details>
<summary><strong>Stats & Insights (6 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_top_tracks` | Your top tracks by time range |
| `spotify_top_artists` | Your top artists by time range |
| `spotify_recently_played` | Recent listening history |
| `spotify_listening_patterns` | When you listen -- hour and day distributions |
| `spotify_taste_profile` | Genre diversity and niche artist analysis |
| `spotify_playlist_compare` | Compare multiple playlists side by side |

</details>

<details>
<summary><strong>Library (9 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_get_saved_tracks` | Your liked/saved tracks |
| `spotify_save_tracks` | Save tracks to Liked Songs |
| `spotify_remove_saved_tracks` | Remove tracks from Liked Songs |
| `spotify_get_saved_albums` | Your saved albums |
| `spotify_save_albums` | Save albums to library |
| `spotify_remove_saved_albums` | Remove albums from library |
| `spotify_check_saved_tracks` | Check if tracks are in Liked Songs |
| `spotify_check_saved_albums` | Check if albums are in your library |
| `spotify_get_saved_episodes` | Your saved podcast episodes |

</details>

<details>
<summary><strong>Follow & Social (7 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_follow_artists` | Follow artists |
| `spotify_unfollow_artists` | Unfollow artists |
| `spotify_get_followed_artists` | List your followed artists |
| `spotify_check_following_artists` | Check if you follow specific artists |
| `spotify_check_following_users` | Check if you follow specific users |
| `spotify_follow_users` | Follow Spotify users |
| `spotify_unfollow_users` | Unfollow Spotify users |

</details>

<details>
<summary><strong>Shows & Podcasts (8 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_get_saved_shows` | Your saved podcasts and shows |
| `spotify_get_show` | Get show details |
| `spotify_get_show_episodes` | List episodes of a show |
| `spotify_save_shows` | Save shows to your library |
| `spotify_remove_saved_shows` | Remove shows from your library |
| `spotify_check_saved_shows` | Check if shows are in your library |
| `spotify_save_episodes` | Save individual episodes |
| `spotify_get_episode` | Get episode details (duration, resume point) |

</details>

<details>
<summary><strong>Browse (4 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_get_track` | Full track details (popularity, ISRC, preview URL) |
| `spotify_get_album` | Album details with full tracklist |
| `spotify_get_artist` | Artist profile (followers, popularity, genres) |
| `spotify_get_user` | User profile with public playlists |

</details>

<details>
<summary><strong>Playlist Power Tools (6 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_merge_playlists` | Merge multiple playlists into one |
| `spotify_split_playlist_by_artist` | Split a playlist by artist |
| `spotify_deduplicate_playlist` | Remove duplicate tracks |
| `spotify_export_playlist` | Export playlist data |
| `spotify_playlist_diff` | Compare track differences between playlists |
| `spotify_find_playlist_overlaps` | Scan all playlists for shared tracks |

</details>

<details>
<summary><strong>Reports & Analytics (3 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_listening_report` | Full listening profile with genres and stats |
| `spotify_playlist_analysis` | Analyze playlist composition |
| `spotify_taste_evolution` | How your taste has changed over time |

</details>

<details>
<summary><strong>Smart Shuffle (1 tool, 6 strategies)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_smart_shuffle` | Reorder a playlist: variety, alphabetical_artist, chronological, genre_variety, energy_arc, reverse_chronological |

</details>

<details>
<summary><strong>Playlist Generators (4 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_create_radio` | Create a radio playlist from a seed track or artist |
| `spotify_time_capsule` | Snapshot your current top tracks into a playlist |
| `spotify_vibe_playlist` | Create a mood-based playlist |
| `spotify_era_playlist` | Create a decade-themed playlist |

</details>

<details>
<summary><strong>Playlist Curator (4 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_sort_playlist` | Sort by track name, artist, album, duration, or date added |
| `spotify_cleanup_playlist` | Remove unavailable tracks and duplicates |
| `spotify_interleave_playlists` | Interleave tracks from multiple playlists |
| `spotify_playlist_radio` | Create a radio playlist from a playlist's top artists |

</details>

<details>
<summary><strong>Queue Builder (2 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_build_queue` | Add multiple tracks to the queue in order |
| `spotify_queue_from_playlist` | Queue tracks from a playlist |

</details>

<details>
<summary><strong>Vibe Engine (2 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_playlist_vibe` | Analyze a playlist's genre vibe and energy |
| `spotify_find_vibe_matches` | Find tracks that match a playlist's vibe |

</details>

<details>
<summary><strong>Artist Explorer (3 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_artist_deep_dive` | Comprehensive artist deep dive report |
| `spotify_artist_timeline` | Artist's career timeline with all releases |
| `spotify_artist_network` | Map an artist's related artist network |

</details>

<details>
<summary><strong>Find Song (1 tool)</strong></summary>

| Tool | Description |
|------|-------------|
| `spotify_find_song` | Find a song using natural language description |

</details>

<details>
<summary><strong>Library Index (3 tools)</strong></summary>

Sync your full Spotify library to a local index, then let your AI assistant create personalized playlists from songs you actually know and love -- not random catalog tracks.

| Tool | Description |
|------|-------------|
| `spotify_sync_library` | Sync liked songs and your playlists to a local JSON index |
| `spotify_library_stats` | Artist counts, playlist names, and dates -- compact overview for AI reasoning |
| `spotify_query_library` | Filter your library by artist, playlist, date range, track/album name |

**Example workflow:**

> "Make a playlist with my favorite indie rock songs from this year"
>
> AI calls `spotify_library_stats` to see your artist landscape, picks matching artists using its music knowledge, calls `spotify_query_library` with those artists + `added_after="2026-01-01"`, then creates a playlist with songs you already know.

The sync stores data locally at `%LOCALAPPDATA%\spotify-mcp\library.json` (Windows) or `~/.cache/spotify-mcp/library.json` (Linux/Mac). Only syncs playlists you created -- skips followed/saved playlists by others.

</details>

## Setup Options

### Option A: Environment Variables (Recommended)

Set `SPOTIFY_CLIENT_ID` (and optionally `SPOTIFY_CLIENT_SECRET`) in your MCP client config's `env` field. This is the simplest approach.

### Option B: Interactive Setup

```bash
spotify-mcp-setup
```

Walks you through entering credentials and saves them to `~/.config/spotify-mcp/.env` (Linux/Mac) or `%APPDATA%\spotify-mcp\.env` (Windows).

### Option C: Manual .env File

Create `.env` in `~/.config/spotify-mcp/` (or `%APPDATA%\spotify-mcp\` on Windows):

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

Add `SPOTIFY_CLIENT_SECRET=your_secret` if you prefer the traditional OAuth flow over PKCE.

### Authentication Modes

- **PKCE (default):** Only needs `SPOTIFY_CLIENT_ID`. No client secret required. Recommended for most users.
- **OAuth:** If `SPOTIFY_CLIENT_SECRET` is also set, uses the traditional OAuth flow. Backward-compatible with existing setups.

## Finding Spotify IDs

Most tools accept Spotify IDs, URIs, or URLs interchangeably:

- **Search first:** Use `spotify_search` to find anything by name
- **Copy from Spotify:** Right-click any item -> Share -> Copy Spotify URI
- **From URLs:** `https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC` -> `4uLU6hMCjMI75M1A2tKUQC`

## A note on Spotify's Feb 2026 API changes

Spotify [removed a bunch of endpoints](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security) in February 2026: `audio-features`, `audio-analysis`, `recommendations`, `artist/top-tracks`, all batch endpoints, and `browse/categories`. Search is now capped at 10 results per page. Most Spotify MCP servers just... broke.

This server was built with those constraints in mind. Discovery uses **search + related artists + genre mapping** instead of the old recommendations API. The vibe engine estimates energy from artist genre data rather than the now-dead audio-features endpoint. It's not perfect, but it works.

## Architecture

```
spotify_mcp/
├── server.py                      # FastMCP entry + toolset loading
├── auth.py                        # OAuth / PKCE auth singleton
├── config.py                      # Constants, genre maps, toolset definitions
├── tools/                         # Core tools (playback, playlists, search, etc.)
├── power/                         # Power tools (smart shuffle, vibe engine, etc.)
└── utils/                         # Shared utilities (client, errors, formatting)
```

## Troubleshooting

### "No active device found"
Open Spotify on any device before using playback commands.

### OAuth redirect fails
Ensure the redirect URI in your config **exactly** matches the Spotify Developer Dashboard. Default: `http://127.0.0.1:8888/callback` (not https).

### Token expired or corrupted
Delete `.spotify_token_cache` from `~/.cache/spotify-mcp/` (or `%LOCALAPPDATA%\spotify-mcp\`) and restart.

### Premium-only features
Volume, seek, transfer, shuffle, and repeat require Spotify Premium.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code conventions, and how to add new tools.

## License

[MIT](LICENSE)

---

If this is useful to you, a star on the repo goes a long way. It helps other people find it.
