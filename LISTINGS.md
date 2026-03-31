# Getting Discovered

The 3 places that actually drive adoption, plus a batch of directories you can knock out in 30 minutes.

---

## 1. Official MCP Registry

The canonical registry. This is where MCP clients will discover and install servers. Long-term this is the most important listing.

- **URL:** https://registry.modelcontextprotocol.io
- **How:** CLI tool from https://github.com/modelcontextprotocol/registry
  ```bash
  git clone https://github.com/modelcontextprotocol/registry
  cd registry && make publisher
  ./bin/mcp-publisher login
  ./bin/mcp-publisher publish
  ```
- **Needs:** `server.json` in repo root (already done)

## 2. Reddit

Post with a screen recording or GIF. Text-only "I made a thing" posts get 20-50 upvotes; demos get 200-500+.

**Where to post (in order):**
1. **r/mcp** (103k) -- the MCP subreddit. No Spotify server posted there yet. Use `[server]` flair.
2. **r/ClaudeAI** (675k) -- largest relevant audience. MCP posts get 900-1500+ upvotes but the bar is high. Need a hook, not just an announcement.
3. **r/ClaudeCode** (189k) -- technical audience that actually uses MCP servers daily.

- **Title style:** "I built a 100+ tool Spotify MCP server" (first person, not salesy)
- **Must include:** Short screen recording showing Claude actually controlling Spotify. Show the interesting tools: "find that sad piano song from the 2000s", smart shuffle, vibe analysis.
- **When:** Tuesday through Thursday, morning US Eastern time
- **Don't:** Cross-post the exact same text. Tailor for each sub.

## 3. Hacker News Show HN

MCP-related Show HN posts have been getting 100-300+ points. Spotify is tangible and demo-friendly, which helps on HN where abstract developer tooling gets ignored.

- **URL:** https://news.ycombinator.com/submit
- **Title:** `Show HN: Spotify MCP Server – 100+ tools to control Spotify from Claude/Cursor`
- **Post at:** 8-9 AM ET on a weekday (Tue-Thu best)
- **First comment:** Have a top-level comment ready explaining what MCP is in one sentence, what makes this different, and the Feb 2026 API story ("Spotify killed a bunch of endpoints, most MCP servers broke, I built this one to work without them")

## Directories (batch in 30 min)

These are all secondary but free and quick. Do them in one sitting:

| Directory | Submit URL | How |
|-----------|-----------|-----|
| mcpservers.org | https://mcpservers.org/submit | Web form (also covers wong2/awesome-mcp-servers) |
| Smithery.ai | https://smithery.ai/server/new | GitHub login, point at repo |
| Glama.ai | https://glama.ai/mcp/servers/new | GitHub login, "Add Server" |
| mcp.so | https://mcp.so/submit | Web form, paste GitHub URL |
| appcypher/awesome-mcp-servers | [GitHub PR](#appcypher-pr-details) | PR to add entry (details below) |

### appcypher PR details

There's already a `varunneal/spotify-mcp` entry under Social Media. Add ours next to it as a second implementation.

**Add below existing Spotify entry:**
```markdown
- <img src="https://cdn.simpleicons.org/spotify/1DB954" height="14"/> [Spotify](https://github.com/gupta-kush/spotify-mcp)<sup><sup>2</sup></sup> - Control Spotify with 100+ tools: playback, search, smart shuffle, vibe analysis, natural language song search, playlist management, and library indexing.
```

**Update existing entry** to add superscript 1 after its link closing paren.

**PR title:** `Add gupta-kush/spotify-mcp to Social Media`

---

## Reusable Copy

**One-liner:**
> Control Spotify from Claude, Cursor, or any MCP client. 100+ tools for playback, playlists, discovery, and curation.

**One paragraph:**
> Control Spotify from Claude, Cursor, or any MCP client. 100+ tools covering playback, search, playlist management, smart shuffle with energy arcs, natural language song search ("find that sad piano song from the 2000s"), artist network mapping, vibe analysis, taste evolution tracking, playlist diff/merge/dedup, and library indexing. Only needs a Spotify Client ID to get started (PKCE auth, no client secret).
