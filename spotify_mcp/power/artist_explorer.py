"""Artist exploration tools — timeline and network mapping."""

import logging
import time
from collections import Counter
from ..utils.spotify_client import get_client, get_artist_cached
from ..utils.pagination import fetch_artist_albums
from ..utils.formatting import format_artist_list, format_album
from ..config import API_SLEEP_SECONDS

logger = logging.getLogger(__name__)


def _group_albums_by_year(albums: list) -> dict:
    """Group albums by release year, returning {year: [albums]}."""
    by_year = {}
    for album in albums:
        release_date = album.get("release_date", "")
        year = release_date[:4] if len(release_date) >= 4 else "Unknown"
        by_year.setdefault(year, []).append(album)
    return by_year


def _type_badge(album: dict) -> str:
    """Return a markdown badge for the album type."""
    atype = album.get("album_type", "album")
    labels = {
        "album": "[Album]",
        "single": "[Single]",
        "compilation": "[Compilation]",
    }
    return labels.get(atype, f"[{atype.title()}]")


def register(mcp):

    @mcp.tool()
    def spotify_artist_timeline(artist_id: str) -> str:
        """Map an artist's full release timeline, grouped by year.

        Shows career span, release counts by type (album/single/compilation),
        and a chronological list of every release with type badges.

        Args:
            artist_id: Spotify artist ID. Get this from search results.
        """
        try:
            sp = get_client()

            # Get artist name
            artist = sp.artist(artist_id)
            name = artist.get("name", "Unknown")

            # Fetch all albums
            albums = fetch_artist_albums(
                sp, artist_id, include_groups="album,single,compilation"
            )

            if not albums:
                return f"# {name} — Timeline\n\nNo releases found."

            # Sort by release date
            albums.sort(key=lambda a: a.get("release_date", ""))

            # Career span
            first_date = albums[0].get("release_date", "Unknown")
            last_date = albums[-1].get("release_date", "Unknown")
            first_year = first_date[:4] if len(first_date) >= 4 else "?"
            last_year = last_date[:4] if len(last_date) >= 4 else "?"

            # Counts by type
            type_counter = Counter(
                a.get("album_type", "album") for a in albums
            )

            # Group by year
            by_year = _group_albums_by_year(albums)

            # Build report
            lines = [
                f"# {name} — Release Timeline",
                "",
                f"**Career span:** {first_year} to {last_year}",
                f"**Total releases:** {len(albums)}",
                "",
                "## Release Counts",
                "",
            ]

            for atype in ["album", "single", "compilation"]:
                count = type_counter.get(atype, 0)
                if count:
                    lines.append(f"- **{atype.title()}s:** {count}")

            lines.append("")
            lines.append("## Chronological Releases")
            lines.append("")

            for year in sorted(by_year.keys()):
                year_albums = by_year[year]
                lines.append(f"### {year} ({len(year_albums)} releases)")
                lines.append("")
                for album in year_albums:
                    badge = _type_badge(album)
                    album_name = album.get("name", "Unknown")
                    release_date = album.get("release_date", "Unknown")
                    lines.append(
                        f"- {badge} **{album_name}** ({release_date})"
                    )
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Artist timeline failed: {e}")
            return f"**Error:** {e}"

    @mcp.tool()
    def spotify_artist_network(artist_id: str, depth: int = 1) -> str:
        """Map an artist's network of related artists.

        Depth 1 shows direct related artists. Depth 2 extends to related
        artists of the top 5 related artists, revealing bridge artists
        (those appearing in multiple related lists) and shared genres.

        Args:
            artist_id: Spotify artist ID. Get this from search results.
            depth: Network depth — 1 for direct only, 2 for extended (default 1).
        """
        depth = max(1, min(2, depth))

        try:
            sp = get_client()

            # Source artist info
            source = get_artist_cached(sp, artist_id)
            source_name = source.get("name", "Unknown")

            # Layer 1: direct related artists
            related_resp = sp.artist_related_artists(artist_id)
            layer1 = related_resp.get("artists", [])[:20]

            if not layer1:
                return (
                    f"# {source_name} — Artist Network\n\n"
                    "No related artists found."
                )

            # Track which related lists each artist appears in (for bridge detection)
            # Key: artist_id, Value: set of source artist names
            appearance_map = {}
            for a in layer1:
                aid = a.get("id", "")
                appearance_map.setdefault(aid, set()).add(source_name)

            # Collect all artists by ID for deduplication
            all_artists = {a.get("id"): a for a in layer1}

            # Layer 2 (if depth == 2)
            layer2 = []
            if depth == 2:
                # Take top 5 from layer 1
                top5 = layer1[:5]
                for i, related_artist in enumerate(top5):
                    raid = related_artist.get("id", "")
                    rname = related_artist.get("name", "Unknown")
                    try:
                        sub_resp = sp.artist_related_artists(raid)
                        sub_related = sub_resp.get("artists", [])[:20]
                        for a in sub_related:
                            aid = a.get("id", "")
                            # Skip source artist
                            if aid == artist_id:
                                continue
                            appearance_map.setdefault(aid, set()).add(rname)
                            if aid not in all_artists:
                                all_artists[aid] = a
                                layer2.append(a)
                    except Exception as e:
                        logger.warning(
                            f"Could not fetch related for {rname}: {e}"
                        )
                    if i < len(top5) - 1:
                        time.sleep(API_SLEEP_SECONDS)

                # Cap layer 2 at ~100 unique total
                if len(layer2) > 100:
                    layer2 = layer2[:100]

            # Identify bridge artists (appear in 2+ related lists)
            bridge_artists = []
            for aid, sources in appearance_map.items():
                if len(sources) >= 2 and aid != artist_id:
                    artist_data = all_artists.get(aid)
                    if artist_data:
                        bridge_artists.append(
                            (artist_data, len(sources), sources)
                        )
            bridge_artists.sort(key=lambda x: x[1], reverse=True)

            # Genre stats across entire network
            genre_counter = Counter()
            for a in all_artists.values():
                for genre in a.get("genres", []):
                    genre_counter[genre] += 1

            # Build report
            lines = [
                f"# {source_name} — Artist Network (Depth {depth})",
                "",
                f"**Source:** {source_name}",
                f"**Network size:** {len(all_artists)} unique artists",
                "",
            ]

            # Layer 1
            lines.append(
                f"## Layer 1 — Direct ({len(layer1)} artists)"
            )
            lines.append("")
            lines.append(format_artist_list(layer1))
            lines.append("")

            # Layer 2
            if depth == 2 and layer2:
                lines.append(
                    f"## Layer 2 — Extended ({len(layer2)} artists)"
                )
                lines.append("")
                lines.append(format_artist_list(layer2))
                lines.append("")

            # Genre stats
            if genre_counter:
                lines.append("## Top Genres Across Network")
                lines.append("")
                for rank, (genre, count) in enumerate(
                    genre_counter.most_common(10), 1
                ):
                    bar_len = int((count / genre_counter.most_common(1)[0][1]) * 15)
                    bar = "\u2588" * bar_len
                    lines.append(f"{rank}. **{genre}** {bar} ({count})")
                lines.append("")

            # Bridge artists
            if bridge_artists:
                lines.append(
                    f"## Bridge Artists ({len(bridge_artists)} found)"
                )
                lines.append("")
                lines.append(
                    "_Artists that appear in multiple related-artist lists, "
                    "connecting different parts of the network._"
                )
                lines.append("")
                for artist_data, count, sources in bridge_artists[:15]:
                    aname = artist_data.get("name", "Unknown")
                    source_list = ", ".join(sorted(sources))
                    lines.append(
                        f"- **{aname}** — shared by {count} artists "
                        f"({source_list})"
                    )
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Artist network failed: {e}")
            return f"**Error:** {e}"
