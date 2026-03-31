# Directory Listings & Submission Guide

Ready-to-paste copy for every MCP directory. Submit in this order (earlier ones feed into later ones).

---

## Short Descriptions (reuse everywhere)

**One-liner (under 80 chars):**
> Spotify MCP server with 100+ tools. Works after the Feb 2026 API changes.

**Medium (1 paragraph):**
> Spotify MCP server with 100+ tools. Goes well beyond play/pause: smart shuffle with energy arcs, natural language song search ("find that sad piano song from the 2000s"), artist network mapping, vibe analysis, taste evolution tracking, playlist merge/diff/dedup, library indexing. Built for Spotify's post-February 2026 API. PKCE auth, no client secret needed.

**Feature bullets (for forms that ask for features):**
- 100+ tools across playback, playlists, search, library, discovery, analytics, and curation
- Smart Shuffle with 6 strategies including energy arcs (chill to hype to chill)
- Natural language song finder: "that sad song with strings by Pink Floyd from the 90s"
- Vibe engine: mood analysis without the deprecated audio-features API
- Artist network mapping: explore 100 connected artists
- Taste evolution: how your listening has changed over time
- Playlist diff, merge, deduplicate, subset detection, and cleanup tools
- Works after Spotify's February 2026 API deprecations
- PKCE auth, only a Client ID needed, no client secret
- Configurable toolsets for clients with tool limits (Cursor: `--toolsets=core`)

---

## Tier 1: Highest Impact (do these first)

### 1. punkpeye/awesome-mcp-servers (PR → also syncs to Glama.ai)

**How:** Fork https://github.com/punkpeye/awesome-mcp-servers, edit README.md, submit PR.

**Category:** `### 🎨 Art & Culture` (where music tools live)

**Entry to add** (insert alphabetically, after entries starting with "s", before "t"):
```markdown
- [gupta-kush/spotify-mcp](https://github.com/gupta-kush/spotify-mcp) 🐍 ☁️ - 100+ tool Spotify server. Smart shuffle, natural language song search, vibe analysis, artist network mapping, taste evolution, playlist diff/merge/dedup. Works after Spotify's Feb 2026 API changes.
```

**PR title:**
```
Add gupta-kush/spotify-mcp to Art & Culture 🤖🤖🤖
```
(The robot emojis opt in to fast-tracked merging)

**PR body:**
```
Adding my Spotify MCP server (100+ tools) to Art & Culture.

The existing Spotify entry (spotify-bulk-actions-mcp) has 18 tools focused on
bulk operations. This one covers playback, search, library management, plus
things like smart shuffle with energy arcs, natural language song search,
artist network mapping, vibe analysis, and playlist diff/merge/dedup.

Published on PyPI (`uvx spotify-mcp`), PKCE auth, works after Spotify's
February 2026 API deprecations.
```

---

### 2. appcypher/awesome-mcp-servers (PR)

**How:** Fork https://github.com/appcypher/awesome-mcp-servers, edit README.md, submit PR.

**Category:** `## 📱 Social Media`

**Entry to add** (at bottom of Social Media section, alongside existing inactive varunneal entry):

The existing entry is:
```markdown
- <img src="https://cdn.simpleicons.org/spotify/1DB954" height="14"/> [Spotify](https://github.com/varunneal/spotify-mcp) - Connects with Spotify for playback control and track/album/artist/playlist management.
```

Add this below it:
```markdown
- <img src="https://cdn.simpleicons.org/spotify/1DB954" height="14"/> [Spotify](https://github.com/gupta-kush/spotify-mcp) - 100+ tool Spotify server. Smart shuffle, natural language song search, vibe analysis, artist network mapping, playlist diff/merge/dedup.
```

**PR title:**
```
Add gupta-kush/spotify-mcp (100+ tool Spotify MCP server)
```

**PR body:**
```
Adding my Spotify MCP server alongside the existing entry.

varunneal/spotify-mcp looks inactive (last commit March 2025, ~15 tools).
This one has 100+ tools covering playback, search, library, smart shuffle,
vibe analysis, artist network mapping, natural language song finder, taste
evolution, and playlist operations. Works after Spotify's Feb 2026 API changes.

Published on PyPI: `uvx spotify-mcp`
```

---

### 3. Official MCP Registry (registry.modelcontextprotocol.io)

**How:** Install and run the `mcp-publisher` CLI:
```bash
npm install -g mcp-publisher
mcp-publisher init    # creates mcp-registry.json in your repo
mcp-publisher login   # authenticates with GitHub
mcp-publisher publish # publishes to the registry
```

**What it needs:** A `mcp-registry.json` file in your repo root. The CLI generates it interactively, but here's what to fill in:

- **Name:** `spotify-mcp`
- **Display Name:** `Spotify MCP Server`
- **Description:** Spotify MCP server with 100+ tools. Smart shuffle, natural language song search, vibe analysis, artist network mapping, taste evolution, playlist diff/merge/dedup. Works after Spotify's Feb 2026 API changes.
- **Category:** `media` or `entertainment`
- **Repository:** `https://github.com/gupta-kush/spotify-mcp`
- **Install command:** `uvx spotify-mcp`

**Cascade:** PulseMCP pulls from this registry, so you may get listed there automatically.

---

### 4. Smithery.ai

**How:** Go to https://smithery.ai, sign in with GitHub, click "Add Server" or use their CLI:
```bash
npx @anthropic-ai/smithery-cli publish https://github.com/gupta-kush/spotify-mcp
```

**What it needs:**
- GitHub repo URL (it pulls README, description, etc.)
- The listing is auto-generated from your repo

---

## Tier 2: Major Directories

### 5. Glama.ai

**How:** Go to https://glama.ai/mcp/servers, click "Add Server", authenticate with GitHub.

**Note:** If punkpeye/awesome-mcp-servers PR is merged, Glama picks it up automatically. Submit here too for faster listing.

- **GitHub URL:** `https://github.com/gupta-kush/spotify-mcp`
- Glama auto-generates the listing from your README

---

### 6. PulseMCP

**How:** Go to https://pulsemcp.com, click "Submit Server" button, or email hello@pulsemcp.com

**Fields:**
- **Name:** Spotify MCP Server
- **URL:** `https://github.com/gupta-kush/spotify-mcp`
- **Description:** Spotify MCP server with 100+ tools. Smart shuffle, natural language song search, vibe analysis, artist network mapping, taste evolution, playlist diff/merge/dedup. Works after Spotify's Feb 2026 API changes. PKCE auth, configurable toolsets.
- **Category:** Media / Entertainment

---

### 7. mcp.so

**How:** Go to https://mcp.so, click "Submit" in the nav bar.

**Fields:**
- **GitHub URL:** `https://github.com/gupta-kush/spotify-mcp`
- Auto-populates from README

---

### 8. MCPServers.org

**How:** Go to https://mcpservers.org/submit (web form).

**Fields:**
- **Name:** Spotify MCP Server
- **URL:** `https://github.com/gupta-kush/spotify-mcp`
- **Description:** (use medium description from top of this file)

---

### 9. MCPMarket.com

**How:** Go to https://mcpmarket.com/submit (web form).

**Fields:**
- **Name:** Spotify MCP Server
- **URL:** `https://github.com/gupta-kush/spotify-mcp`
- **Logo:** 400x400 PNG (you'll need to create one)
- **Description:** (use medium description from top of this file)

---

### 10. Cursor Directory

**How:** Go to https://cursor.directory, look for plugin/MCP submission.

**Fields:**
- **Name:** Spotify MCP Server
- **Install:** `uvx spotify-mcp --toolsets=core`
- **Description:** (use medium description, emphasize `--toolsets=core` for Cursor's 40-tool limit)

---

### 11. Docker MCP Catalog

**How:** PR to https://github.com/docker/mcp-registry

**Note:** Requires a Docker image. You'd need to create a Dockerfile first. Lower priority unless you want Docker distribution.

---

### 12. Cline MCP Marketplace

**How:** Open a GitHub issue at https://github.com/cline/mcp-marketplace with your repo URL and a logo.

---

### 13. LobeHub

**How:** PR to https://github.com/lobehub/lobe-chat-plugins to add your server to their plugin index.

---

## Tier 3: Smaller Directories (week 2-3)

These are mostly web forms. Use the medium description and GitHub URL for all of them:

- MCPIndex.net
- MCPServerFinder.com
- MCPServers.net
- MCPServerDirectory.org
- MCPShowcase.com
- AIAgentsList.com
- MCPFinder.dev
- AIxploria
- Playbooks.com/mcp
- APITracker.io
- Portkey.ai

---

## GitHub Repo Settings (do now)

**Topics** (Settings → General → Topics):
```
mcp, model-context-protocol, spotify, claude, ai, python, mcp-server, fastmcp, spotify-api, llm-tools
```

**Description** (Settings → General):
```
Spotify MCP server with 100+ tools. Smart shuffle, vibe analysis, natural language song search, artist network mapping, playlist diff/merge/dedup, library indexing.
```

**Website** (Settings → General):
```
https://pypi.org/project/spotify-mcp/
```

**Social Preview** (Settings → General → Social Preview):
Upload a 1280x640 image. You'll need to create this.
