# Spotify MCP Server

[![PyPI](https://img.shields.io/pypi/v/spotify-mcp)](https://pypi.org/project/spotify-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

The most comprehensive Spotify MCP server available. **93 tools** for playback control, playlist management, music discovery, listening analytics, and more -- all accessible through the [Model Context Protocol](https://modelcontextprotocol.io/).

## Highlights

- **93 tools** -- more than any other Spotify MCP server
- **Smart features:** vibe engine, smart shuffle (6 strategies), natural language song search, artist network mapping
- **Power tools:** playlist merge/diff/deduplicate, listening reports, taste evolution tracking
- **Full coverage:** playback, playlists, library, podcasts, follow management, search, browse
- **Works with Spotify's Feb 2026 API** -- handles deprecated endpoints gracefully with search + genre-based alternatives

## Quick Start

### Install

```bash
uvx spotify-mcp
```

Or with pip:

```bash
pip install spotify-mcp
```

### Configure Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": ["spotify-mcp"]
    }
  }
}
```

## Setup

### Prerequisites

- Python 3.10 or higher
- A Spotify account (Premium required for playback control features)

### 1. Create a Spotify Developer App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Fill in an app name and description (anything is fine)
4. Set the **Redirect URI** to `http://127.0.0.1:8888/callback`
5. Check the **Web API** checkbox
6. Click **Save**
7. Copy your **Client ID** and **Client Secret** from the app settings

### 2. Configure Credentials

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your Client ID and Client Secret from the dashboard.

### 3. First Run

The first time you run the server, it will open a browser window for Spotify OAuth authorization. Grant access to your account and the token will be cached locally for future use.

### 4. Other Clients

For **Cursor**, **VS Code**, or other MCP-compatible editors, point the MCP configuration to the `spotify-mcp` command:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": ["spotify-mcp"]
    }
  }
}
```

Or if running from source:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "path/to/.venv/Scripts/python.exe",
      "args": ["-m", "spotify_mcp.server"]
    }
  }
}
```

## Tool Reference

### Playback (14 tools)

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

### Playlists (12 tools)

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

### Search (1 tool)

| Tool | Description |
|------|-------------|
| `spotify_search` | Search for tracks, artists, albums, or playlists |

### Discovery (5 tools)

| Tool | Description |
|------|-------------|
| `spotify_related_artists` | Find artists similar to a given artist |
| `spotify_discover_by_artist` | Discover tracks via related artists |
| `spotify_discover_by_mood` | Find tracks matching a mood |
| `spotify_genre_explorer` | Explore tracks and artists in a genre |
| `spotify_discover_deep_cuts` | Find album-only tracks (not singles) |

### Stats (3 tools)

| Tool | Description |
|------|-------------|
| `spotify_top_tracks` | Your top tracks by time range |
| `spotify_top_artists` | Your top artists by time range |
| `spotify_recently_played` | Recent listening history |

### Library (9 tools)

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

### Follow (7 tools)

| Tool | Description |
|------|-------------|
| `spotify_follow_artists` | Follow artists |
| `spotify_unfollow_artists` | Unfollow artists |
| `spotify_get_followed_artists` | List your followed artists |
| `spotify_check_following_artists` | Check if you follow specific artists |
| `spotify_check_following_users` | Check if you follow specific users |
| `spotify_follow_users` | Follow Spotify users |
| `spotify_unfollow_users` | Unfollow Spotify users |

### Shows / Podcasts (8 tools)

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

### Browse (4 tools)

| Tool | Description |
|------|-------------|
| `spotify_get_track` | Full track details (popularity, ISRC, preview URL) |
| `spotify_get_album` | Album details with full tracklist |
| `spotify_get_artist` | Artist profile (followers, popularity, genres) |
| `spotify_get_user` | User profile with public playlists |

### Playlist Ops (6 tools)

| Tool | Description |
|------|-------------|
| `spotify_merge_playlists` | Merge multiple playlists into one |
| `spotify_split_playlist_by_artist` | Split a playlist by artist |
| `spotify_deduplicate_playlist` | Remove duplicate tracks |
| `spotify_export_playlist` | Export playlist data |
| `spotify_playlist_diff` | Compare track differences between playlists |
| `spotify_find_playlist_overlaps` | Scan all playlists for shared tracks and merge candidates |

### Reports (3 tools)

| Tool | Description |
|------|-------------|
| `spotify_listening_report` | Full listening profile with genres and stats |
| `spotify_playlist_analysis` | Analyze playlist composition |
| `spotify_taste_evolution` | How your taste has changed over time |

### Smart Shuffle (1 tool, 6 strategies)

| Tool | Description |
|------|-------------|
| `spotify_smart_shuffle` | Intelligent playlist reordering -- variety, alphabetical_artist, chronological, genre_variety, energy_arc, reverse_chronological |

### Deep Dive (1 tool)

| Tool | Description |
|------|-------------|
| `spotify_artist_deep_dive` | Comprehensive artist deep dive report |

### Playlist Generator (4 tools)

| Tool | Description |
|------|-------------|
| `spotify_create_radio` | Create a radio playlist from a seed track or artist |
| `spotify_time_capsule` | Snapshot your current top tracks into a playlist |
| `spotify_vibe_playlist` | Create a mood-based playlist |
| `spotify_era_playlist` | Create a decade-themed playlist |

### Playlist Sort (1 tool)

| Tool | Description |
|------|-------------|
| `spotify_sort_playlist` | Sort a playlist by track name, artist, album, duration, or date added |

### Playlist Curator (3 tools)

| Tool | Description |
|------|-------------|
| `spotify_cleanup_playlist` | Remove unavailable tracks and duplicates |
| `spotify_interleave_playlists` | Interleave tracks from multiple playlists |
| `spotify_playlist_radio` | Create a radio playlist from a playlist's top artists |

### Queue Builder (2 tools)

| Tool | Description |
|------|-------------|
| `spotify_build_queue` | Add multiple tracks to the queue in order |
| `spotify_queue_from_playlist` | Queue tracks from a playlist |

### Vibe Engine (2 tools)

| Tool | Description |
|------|-------------|
| `spotify_playlist_vibe` | Analyze a playlist's genre vibe and energy |
| `spotify_find_vibe_matches` | Find tracks that match a playlist's vibe |

### Insights (3 tools)

| Tool | Description |
|------|-------------|
| `spotify_listening_patterns` | When you listen -- hour and day distributions |
| `spotify_taste_profile` | Genre diversity and niche artist analysis |
| `spotify_playlist_compare` | Compare multiple playlists side by side |

### Artist Explorer (2 tools)

| Tool | Description |
|------|-------------|
| `spotify_artist_timeline` | Artist's career timeline with all releases |
| `spotify_artist_network` | Map an artist's related artist network |

### Find Song (1 tool)

| Tool | Description |
|------|-------------|
| `spotify_find_song` | Find a song using natural language description |

## Example Prompts

- "Play Bohemian Rhapsody"
- "Seek to 2:30"
- "Transfer playback to my phone"
- "Create a radio playlist based on Radiohead"
- "Make me a chill vibe playlist"
- "What's the vibe of my Summer playlist?"
- "Create a time capsule from my all-time favorites"
- "Build a queue of 10 energetic tracks"
- "Sort my workout playlist by artist"
- "Clean up my old playlist -- remove unavailable tracks"
- "Show me my listening patterns"
- "How has my taste evolved over time?"
- "Map Radiohead's related artist network"
- "Find that song that goes 'we're just two lost souls' by Pink Floyd"
- "What podcasts am I following?"
- "Compare my Gym and Running playlists"
- "Interleave my Morning and Evening playlists"
- "Tell me about the album Abbey Road"
- "Who am I following? Am I following Radiohead?"
- "Get the cover art for my playlist"
- "Save that episode for later"

## Finding Spotify IDs

Most tools accept Spotify IDs, URIs, or URLs interchangeably. You can:

- **Search first:** Use `spotify_search` to find anything by name
- **Copy from Spotify:** Right-click any item in Spotify -> Share -> Copy Spotify URI
- **From URLs:** The ID is the last part -- `https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC` -> `4uLU6hMCjMI75M1A2tKUQC`

## API Compatibility

This server is built for Spotify's **February 2026 API** (Development Mode). The following endpoints are no longer available:

- `audio-features` / `audio-analysis`
- `recommendations`
- `artist/top-tracks`
- Batch endpoints (`/tracks`, `/artists`, `/albums`)
- `browse/categories` / `browse/new-releases`
- Search is limited to 10 results per page

Discovery and analysis features use **search + related artists + genre mapping** as alternatives. The vibe engine estimates energy from artist genre data rather than audio features.

## Architecture

```
spotify_mcp/
├── __init__.py                    # Package init + version
├── server.py                      # FastMCP entry + spotify_status
├── auth.py                        # OAuth singleton
├── config.py                      # Constants, genre maps, energy estimates
├── tools/
│   ├── playback.py                # 14 tools — playback control
│   ├── playlists.py               # 12 tools — playlist CRUD
│   ├── search.py                  # 1 tool — search
│   ├── discovery.py               # 5 tools — music discovery
│   ├── stats.py                   # 3 tools — top tracks/artists
│   ├── library.py                 # 9 tools — saved tracks/albums/episodes
│   ├── follow.py                  # 7 tools — artist/user following
│   ├── shows.py                   # 8 tools — podcasts/shows
│   └── browse.py                  # 4 tools — track/album/artist/user lookup
├── power/
│   ├── playlist_ops.py            # 6 tools — bulk playlist ops
│   ├── reports.py                 # 3 tools — listening reports
│   ├── smart_shuffle.py           # 1 tool (6 strategies)
│   ├── deep_dive.py               # 1 tool — artist deep dive
│   ├── playlist_generator.py      # 4 tools — smart playlist creation
│   ├── playlist_sort.py           # 1 tool — playlist sorting
│   ├── playlist_curator.py        # 3 tools — cleanup/interleave/radio
│   ├── queue_builder.py           # 2 tools — queue building
│   ├── vibe_engine.py             # 2 tools — vibe analysis
│   ├── insights.py                # 3 tools — listening insights
│   ├── artist_explorer.py         # 2 tools — artist timeline/network
│   └── find_song.py               # 1 tool — natural language search
└── utils/
    ├── spotify_client.py          # Spotipy client + artist cache
    ├── formatting.py              # Markdown formatters
    ├── pagination.py              # Pagination helpers
    ├── rate_limit.py              # Rate limiting
    └── uri_parser.py              # URI/URL/ID parsing
```

## Troubleshooting

### "No active device found"
Open Spotify on any device (phone, desktop, or web player) before using playback commands. Spotify requires an active device for playback control.

### OAuth redirect fails
Make sure the redirect URI in your `.env` **exactly** matches what you set in the Spotify Developer Dashboard. The default is `http://127.0.0.1:8888/callback` (not https).

### "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"
Copy `.env.example` to `.env` and fill in your credentials from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

### Token expired or corrupted
Delete `.spotify_token_cache` in your project directory and restart. You'll be prompted to re-authorize.

### Premium-only features
Some playback tools (volume, seek, transfer, shuffle, repeat) require Spotify Premium. Free-tier users will see an API error for these.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code conventions, and how to add new tools.

## License

[MIT](LICENSE)
