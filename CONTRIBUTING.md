# Contributing to Spotify MCP

Thanks for your interest in contributing!

## Development Setup

1. Clone the repo and create a virtual environment:
   ```bash
   git clone https://github.com/gupta-kush/spotify-mcp.git
   cd spotify-mcp
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

3. Copy `.env.example` to `.env` and add your Spotify Developer credentials:
   ```bash
   cp .env.example .env
   ```

4. Run the server:
   ```bash
   spotify-mcp
   ```

## Adding a New Tool

1. **Choose the right module:**
   - `spotify_mcp/tools/` -- Standard Spotify API wrappers (playback, playlists, search, etc.)
   - `spotify_mcp/power/` -- Compound operations that combine multiple API calls (smart shuffle, vibe analysis, etc.)

2. **Add your tool** inside the module's `register(mcp)` function using the `@mcp.tool()` decorator.

3. **Follow these conventions:**
   - **Naming:** `spotify_{verb}_{noun}` (e.g., `spotify_create_playlist`, `spotify_merge_playlists`)
   - **Returns:** Always return a markdown-formatted string
   - **Errors:** Return `"**Error:** ..."` strings (don't raise exceptions)
   - **Client:** `from ..utils.spotify_client import get_client` then `sp = get_client()`
   - **Limits:** Clamp with `max(1, min(N, limit))`
   - **Batch ops:** Process playlist items in chunks of 100
   - **Helpers:** Private helpers use `_` prefix, defined at module level outside `register()`

4. **Update the README** tool count and add your tool to the appropriate table.

## Code Style

- Use type hints for function signatures
- Add clear docstrings -- these are shown to LLMs, so be descriptive about parameters and behavior
- Use `logging.getLogger(__name__)` for logging
- Use relative imports (`from ..utils.X import ...`)
