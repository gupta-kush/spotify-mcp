"""Mocked integration tests for the top 15 Spotify MCP tools.

Each test mocks ``get_client`` (and other dependencies) so that no real
Spotify API calls are made.  For every tool we verify:
  - happy-path: returns a string containing expected content
  - error-path: returns a string containing ``**Error:**``
"""

import pytest
from unittest.mock import patch, MagicMock

from spotipy.exceptions import SpotifyException
from mcp.server.fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Helpers to build realistic fake Spotify API data
# ---------------------------------------------------------------------------

def _make_track(
    name="Test Song",
    artist="Test Artist",
    album="Test Album",
    duration_ms=210_000,
    track_id="6rqhFgbbKwnb9MLmUQDhG6",
    uri="spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
    popularity=72,
    explicit=False,
    track_number=1,
    disc_number=1,
    release_date="2024-06-15",
    total_tracks=12,
):
    """Build a minimal track dict matching the Spotify API shape."""
    return {
        "id": track_id,
        "name": name,
        "uri": uri,
        "artists": [{"name": artist, "id": "artist123", "uri": "spotify:artist:artist123"}],
        "album": {
            "name": album,
            "release_date": release_date,
            "total_tracks": total_tracks,
        },
        "duration_ms": duration_ms,
        "popularity": popularity,
        "explicit": explicit,
        "track_number": track_number,
        "disc_number": disc_number,
        "external_urls": {"spotify": f"https://open.spotify.com/track/{track_id}"},
        "external_ids": {"isrc": "USAT21301111"},
        "preview_url": "https://p.scdn.co/mp3-preview/abc",
    }


def _make_artist(
    name="Test Artist",
    artist_id="artist123",
    genres=None,
    followers=1_000_000,
    popularity=85,
):
    """Build a minimal artist dict."""
    return {
        "id": artist_id,
        "name": name,
        "genres": genres or ["rock", "indie"],
        "followers": {"total": followers},
        "popularity": popularity,
        "images": [{"url": "https://i.scdn.co/image/abc", "width": 640, "height": 640}],
        "external_urls": {"spotify": f"https://open.spotify.com/artist/{artist_id}"},
    }


def _make_playlist(
    name="Test Playlist",
    playlist_id="pl123",
    owner="testuser",
    total_tracks=42,
    public=True,
    description="A great playlist",
):
    """Build a minimal playlist dict."""
    return {
        "id": playlist_id,
        "name": name,
        "owner": {"display_name": owner, "id": owner},
        "tracks": {"total": total_tracks},
        "public": public,
        "description": description,
        "external_urls": {"spotify": f"https://open.spotify.com/playlist/{playlist_id}"},
    }


def _make_playback(
    track=None,
    is_playing=True,
    progress_ms=60_000,
    shuffle=False,
    repeat="off",
    device_name="Desktop",
):
    """Build a minimal current_playback response."""
    if track is None:
        track = _make_track()
    return {
        "item": track,
        "is_playing": is_playing,
        "progress_ms": progress_ms,
        "shuffle_state": shuffle,
        "repeat_state": repeat,
        "device": {
            "name": device_name,
            "type": "Computer",
            "is_active": True,
            "volume_percent": 65,
        },
    }


def _make_spotify_exception(http_status, msg="", reason="", headers=None):
    """Create a SpotifyException for error tests."""
    return SpotifyException(http_status, -1, msg, reason=reason, headers=headers)


# ---------------------------------------------------------------------------
# Fixture: build a fresh FastMCP and register all tool modules
# ---------------------------------------------------------------------------

@pytest.fixture()
def tool_registry():
    """Create a FastMCP instance, register each module, and return a
    helper dict mapping tool-name -> callable function.

    We mock ``get_client`` at import time (inside the modules) to return
    a MagicMock — but individual tests may override via monkeypatching.
    """
    test_mcp = FastMCP(name="TestSpotify")

    # Register each module under test
    from spotify_mcp.tools.playback import register as reg_playback
    from spotify_mcp.tools.search import register as reg_search
    from spotify_mcp.tools.playlists import register as reg_playlists
    from spotify_mcp.tools.stats import register as reg_stats
    from spotify_mcp.tools.library import register as reg_library
    from spotify_mcp.tools.browse import register as reg_browse
    from spotify_mcp.power.smart_shuffle import register as reg_smart_shuffle
    from spotify_mcp.power.find_song import register as reg_find_song
    from spotify_mcp.power.playlist_ops import register as reg_playlist_ops

    reg_playback(test_mcp)
    reg_search(test_mcp)
    reg_playlists(test_mcp)
    reg_stats(test_mcp)
    reg_library(test_mcp)
    reg_browse(test_mcp)
    reg_smart_shuffle(test_mcp)
    reg_find_song(test_mcp)
    reg_playlist_ops(test_mcp)

    # Build a tool-name -> fn lookup
    tools = {}
    for tool in test_mcp._tool_manager.list_tools():
        tools[tool.name] = tool.fn
    return tools


@pytest.fixture()
def mock_sp():
    """Return a fresh MagicMock that acts as a Spotipy client."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Helper to patch get_client across all modules that import it
# ---------------------------------------------------------------------------

def _patch_get_client(mock_sp):
    """Return a list of active patchers that replace get_client everywhere."""
    targets = [
        "spotify_mcp.utils.spotify_client.get_client",
        "spotify_mcp.tools.playback.get_client",
        "spotify_mcp.tools.search.get_client",
        "spotify_mcp.tools.playlists.get_client",
        "spotify_mcp.tools.stats.get_client",
        "spotify_mcp.tools.library.get_client",
        "spotify_mcp.tools.browse.get_client",
        "spotify_mcp.power.smart_shuffle.get_client",
        "spotify_mcp.power.find_song.get_client",
        "spotify_mcp.power.playlist_ops.get_client",
    ]
    patchers = []
    for target in targets:
        p = patch(target, return_value=mock_sp)
        p.start()
        patchers.append(p)
    return patchers


@pytest.fixture(autouse=True)
def auto_patch_get_client(mock_sp):
    """Automatically patch get_client for every test in this module."""
    patchers = _patch_get_client(mock_sp)
    yield
    for p in patchers:
        p.stop()


# ===========================================================================
# 1. spotify_status (defined directly in server.py)
# ===========================================================================


class TestSpotifyStatus:
    """Tests for spotify_status in server.py.

    spotify_status imports get_client lazily inside its body via
    ``from .utils.spotify_client import get_client``, so we patch
    the canonical location that the auto_patch_get_client fixture
    already covers.
    """

    def test_happy_path(self, mock_sp):
        mock_sp.me.return_value = {"display_name": "John", "id": "john123"}
        mock_sp.current_playback.return_value = _make_playback()

        from spotify_mcp.server import spotify_status
        result = spotify_status()

        assert isinstance(result, str)
        assert "John" in result
        assert "john123" in result
        assert "Test Song" in result

    def test_nothing_playing(self, mock_sp):
        mock_sp.me.return_value = {"display_name": "Jane", "id": "jane456"}
        mock_sp.current_playback.return_value = None

        from spotify_mcp.server import spotify_status
        result = spotify_status()

        assert isinstance(result, str)
        assert "Nothing currently playing" in result

    def test_playback_exception(self, mock_sp):
        mock_sp.me.return_value = {"display_name": "Error User", "id": "err"}
        mock_sp.current_playback.side_effect = _make_spotify_exception(500, msg="Server Error")

        from spotify_mcp.server import spotify_status
        result = spotify_status()

        assert isinstance(result, str)
        assert "Could not fetch" in result


# ===========================================================================
# 2. spotify_now_playing (tools/playback.py)
# ===========================================================================


class TestSpotifyNowPlaying:

    def test_happy_path(self, tool_registry, mock_sp):
        mock_sp.current_playback.return_value = _make_playback()
        fn = tool_registry["spotify_now_playing"]
        result = fn()

        assert isinstance(result, str)
        assert "**Playing**" in result
        assert "Test Song" in result
        assert "Shuffle" in result

    def test_nothing_playing(self, tool_registry, mock_sp):
        mock_sp.current_playback.return_value = None
        fn = tool_registry["spotify_now_playing"]
        result = fn()

        assert isinstance(result, str)
        assert "Nothing is currently playing" in result

    def test_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.current_playback.side_effect = _make_spotify_exception(
            401, reason="Unauthorized"
        )
        fn = tool_registry["spotify_now_playing"]
        result = fn()

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 3. spotify_play (tools/playback.py)
# ===========================================================================


class TestSpotifyPlay:

    def test_play_uri(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_play"]
        result = fn(uri="spotify:track:abc123")

        assert isinstance(result, str)
        assert "Now playing" in result
        assert "spotify:track:abc123" in result
        mock_sp.start_playback.assert_called_once_with(uris=["spotify:track:abc123"])

    def test_resume_playback(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_play"]
        result = fn()

        assert isinstance(result, str)
        assert "Playback resumed" in result
        mock_sp.start_playback.assert_called_once_with()

    def test_play_context_uri(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_play"]
        result = fn(context_uri="spotify:album:xyz789")

        assert isinstance(result, str)
        assert "Now playing" in result
        assert "spotify:album:xyz789" in result

    def test_spotify_exception_no_device(self, tool_registry, mock_sp):
        mock_sp.start_playback.side_effect = _make_spotify_exception(
            403, msg="Player command failed: No active device found"
        )
        fn = tool_registry["spotify_play"]
        result = fn()

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 4. spotify_search (tools/search.py)
# ===========================================================================


class TestSpotifySearch:

    def test_search_tracks(self, tool_registry, mock_sp):
        track = _make_track(name="Bohemian Rhapsody", artist="Queen")
        mock_sp.search.return_value = {
            "tracks": {
                "items": [track],
                "next": None,
            },
        }
        fn = tool_registry["spotify_search"]
        result = fn(query="Bohemian Rhapsody", type="track", limit=5)

        assert isinstance(result, str)
        assert "Bohemian Rhapsody" in result
        assert "Queen" in result

    def test_search_no_results(self, tool_registry, mock_sp):
        mock_sp.search.return_value = {
            "tracks": {"items": [], "next": None},
        }
        fn = tool_registry["spotify_search"]
        result = fn(query="xyznonexistent123", type="track")

        assert isinstance(result, str)
        assert "No results found" in result

    def test_search_invalid_type(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_search"]
        result = fn(query="test", type="invalid_type")

        assert isinstance(result, str)
        assert "**Error:**" in result
        assert "Unknown type" in result

    def test_search_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.search.side_effect = _make_spotify_exception(429, reason="Rate Limited")
        fn = tool_registry["spotify_search"]
        result = fn(query="test")

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 5. spotify_get_my_playlists (tools/playlists.py)
# ===========================================================================


class TestSpotifyGetMyPlaylists:

    def test_happy_path(self, tool_registry, mock_sp):
        playlists = [
            _make_playlist(name="Chill Vibes", playlist_id="pl1", total_tracks=30),
            _make_playlist(name="Workout Mix", playlist_id="pl2", total_tracks=50),
        ]
        mock_sp.current_user_playlists.return_value = {
            "items": playlists,
            "total": 2,
        }
        fn = tool_registry["spotify_get_my_playlists"]
        result = fn()

        assert isinstance(result, str)
        assert "Your Playlists" in result
        assert "Chill Vibes" in result
        assert "Workout Mix" in result

    def test_no_playlists(self, tool_registry, mock_sp):
        mock_sp.current_user_playlists.return_value = {
            "items": [],
            "total": 0,
        }
        fn = tool_registry["spotify_get_my_playlists"]
        result = fn()

        assert isinstance(result, str)
        assert "Your Playlists" in result

    def test_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.current_user_playlists.side_effect = _make_spotify_exception(
            500, reason="Internal Server Error"
        )
        fn = tool_registry["spotify_get_my_playlists"]
        result = fn()

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 6. spotify_get_playlist (tools/playlists.py)
# ===========================================================================


class TestSpotifyGetPlaylist:

    def test_happy_path(self, tool_registry, mock_sp):
        track1 = _make_track(name="Song A", duration_ms=180_000)
        track2 = _make_track(name="Song B", duration_ms=240_000)
        playlist = _make_playlist(name="My Hits", total_tracks=2)
        playlist["tracks"]["items"] = [
            {"track": track1},
            {"track": track2},
        ]
        mock_sp.playlist.return_value = playlist
        fn = tool_registry["spotify_get_playlist"]
        result = fn(playlist_id="pl123")

        assert isinstance(result, str)
        assert "My Hits" in result
        assert "Song A" in result
        assert "Song B" in result
        assert "Duration" in result

    def test_spotify_exception_not_found(self, tool_registry, mock_sp):
        mock_sp.playlist.side_effect = _make_spotify_exception(
            404, reason="Not Found"
        )
        fn = tool_registry["spotify_get_playlist"]
        result = fn(playlist_id="nonexistent")

        assert isinstance(result, str)
        assert "**Error:**" in result
        assert "not found" in result.lower()


# ===========================================================================
# 7. spotify_create_playlist (tools/playlists.py)
# ===========================================================================


class TestSpotifyCreatePlaylist:

    def test_happy_path(self, tool_registry, mock_sp):
        mock_sp.me.return_value = {"id": "user123"}
        mock_sp.user_playlist_create.return_value = {
            "id": "new_pl_id",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/new_pl_id"},
        }
        fn = tool_registry["spotify_create_playlist"]
        result = fn(name="Road Trip", description="Songs for driving", public=True)

        assert isinstance(result, str)
        assert "Road Trip" in result
        assert "new_pl_id" in result
        mock_sp.user_playlist_create.assert_called_once_with(
            user="user123",
            name="Road Trip",
            public=True,
            description="Songs for driving",
        )

    def test_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.me.side_effect = _make_spotify_exception(
            401, reason="Unauthorized"
        )
        fn = tool_registry["spotify_create_playlist"]
        result = fn(name="New Playlist")

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 8. spotify_add_to_playlist (tools/playlists.py)
# ===========================================================================


class TestSpotifyAddToPlaylist:

    def test_happy_path(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_add_to_playlist"]
        result = fn(
            playlist_id="pl123",
            uris=["spotify:track:aaa", "spotify:track:bbb"],
        )

        assert isinstance(result, str)
        assert "Added 2 track(s)" in result
        assert "pl123" in result
        mock_sp.playlist_add_items.assert_called_once()

    def test_empty_uris(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_add_to_playlist"]
        result = fn(playlist_id="pl123", uris=[])

        assert isinstance(result, str)
        assert "**Error:**" in result
        assert "No track URIs" in result

    def test_too_many_uris(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_add_to_playlist"]
        uris = [f"spotify:track:id{i}" for i in range(101)]
        result = fn(playlist_id="pl123", uris=uris)

        assert isinstance(result, str)
        assert "**Error:**" in result
        assert "100" in result

    def test_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.playlist_add_items.side_effect = _make_spotify_exception(
            403, reason="Forbidden"
        )
        fn = tool_registry["spotify_add_to_playlist"]
        result = fn(playlist_id="pl123", uris=["spotify:track:aaa"])

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 9. spotify_top_tracks (tools/stats.py)
# ===========================================================================


class TestSpotifyTopTracks:

    def test_happy_path(self, tool_registry, mock_sp):
        tracks = [
            _make_track(name=f"Top Song {i}", track_id=f"id{i}", uri=f"spotify:track:id{i}")
            for i in range(3)
        ]
        mock_sp.current_user_top_tracks.return_value = {"items": tracks}
        fn = tool_registry["spotify_top_tracks"]
        result = fn(time_range="short_term", limit=3)

        assert isinstance(result, str)
        assert "Top Tracks" in result
        assert "last 4 weeks" in result
        assert "Top Song 0" in result

    def test_invalid_time_range(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_top_tracks"]
        result = fn(time_range="invalid_range")

        assert isinstance(result, str)
        assert "**Error:**" in result
        assert "time_range" in result

    def test_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.current_user_top_tracks.side_effect = _make_spotify_exception(
            500, reason="Internal Server Error"
        )
        fn = tool_registry["spotify_top_tracks"]
        result = fn()

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 10. spotify_get_saved_tracks (tools/library.py)
# ===========================================================================


class TestSpotifyGetSavedTracks:

    def test_happy_path(self, tool_registry, mock_sp):
        tracks = [
            {"track": _make_track(name="Liked Song 1")},
            {"track": _make_track(name="Liked Song 2")},
        ]
        mock_sp.current_user_saved_tracks.return_value = {
            "items": tracks,
            "total": 100,
        }
        fn = tool_registry["spotify_get_saved_tracks"]
        result = fn(limit=10, offset=0)

        assert isinstance(result, str)
        assert "Liked Songs" in result
        assert "Liked Song 1" in result

    def test_empty_library(self, tool_registry, mock_sp):
        mock_sp.current_user_saved_tracks.return_value = {
            "items": [],
            "total": 0,
        }
        fn = tool_registry["spotify_get_saved_tracks"]
        result = fn()

        assert isinstance(result, str)
        assert "Liked Songs" in result

    def test_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.current_user_saved_tracks.side_effect = _make_spotify_exception(
            401, reason="Unauthorized"
        )
        fn = tool_registry["spotify_get_saved_tracks"]
        result = fn()

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 11. spotify_get_track (tools/browse.py)
# ===========================================================================


class TestSpotifyGetTrack:

    def test_happy_path(self, tool_registry, mock_sp):
        track = _make_track(
            name="Bohemian Rhapsody",
            artist="Queen",
            album="A Night at the Opera",
            duration_ms=354_000,
            popularity=91,
            explicit=False,
        )
        mock_sp.track.return_value = track
        fn = tool_registry["spotify_get_track"]
        result = fn(track_id="6rqhFgbbKwnb9MLmUQDhG6")

        assert isinstance(result, str)
        assert "Bohemian Rhapsody" in result
        assert "Queen" in result
        assert "A Night at the Opera" in result
        assert "91/100" in result
        assert "Explicit:** No" in result

    def test_spotify_exception_not_found(self, tool_registry, mock_sp):
        mock_sp.track.side_effect = _make_spotify_exception(404, reason="Not Found")
        fn = tool_registry["spotify_get_track"]
        # Must use a valid 22-char Spotify ID (parse_spotify_id validates format)
        result = fn(track_id="6rqhFgbbKwnb9MLmUQDhG6")

        assert isinstance(result, str)
        assert "**Error:**" in result
        assert "not found" in result.lower()


# ===========================================================================
# 12. spotify_get_artist (tools/browse.py)
# ===========================================================================


class TestSpotifyGetArtist:

    def test_happy_path(self, tool_registry, mock_sp):
        artist = _make_artist(
            name="Radiohead",
            genres=["alternative rock", "art rock", "experimental"],
            followers=10_000_000,
            popularity=80,
        )
        mock_sp.artist.return_value = artist
        fn = tool_registry["spotify_get_artist"]
        # Must use a valid 22-char Spotify ID (parse_spotify_id validates format)
        result = fn(artist_id="4Z8W4fKeB5YxbusRsdQVPb")

        assert isinstance(result, str)
        assert "Radiohead" in result
        assert "10,000,000" in result
        assert "80/100" in result
        assert "alternative rock" in result

    def test_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.artist.side_effect = _make_spotify_exception(404, reason="Not Found")
        fn = tool_registry["spotify_get_artist"]
        # Must use a valid 22-char Spotify ID
        result = fn(artist_id="4Z8W4fKeB5YxbusRsdQVPb")

        assert isinstance(result, str)
        assert "**Error:**" in result


# ===========================================================================
# 13. spotify_smart_shuffle (power/smart_shuffle.py)
# ===========================================================================


class TestSpotifySmartShuffle:

    def test_variety_strategy(self, tool_registry, mock_sp):
        # Setup: playlist with tracks by different artists
        tracks = [
            _make_track(name=f"Song {i}", artist=f"Artist {i % 3}",
                        track_id=f"id{i}", uri=f"spotify:track:id{i}")
            for i in range(6)
        ]
        items = [{"track": t} for t in tracks]

        mock_sp.playlist.return_value = {"name": "Party Mix"}
        mock_sp.playlist_items.return_value = {
            "items": items,
            "next": None,
        }
        fn = tool_registry["spotify_smart_shuffle"]
        result = fn(playlist_id="pl123", strategy="variety")

        assert isinstance(result, str)
        assert "Smart Shuffled" in result
        assert "Party Mix" in result
        assert "variety" in result
        assert "6 tracks" in result
        # Verify it replaced and re-added
        mock_sp.playlist_replace_items.assert_called_once()
        assert mock_sp.playlist_add_items.call_count >= 1

    def test_invalid_strategy(self, tool_registry, mock_sp):
        fn = tool_registry["spotify_smart_shuffle"]
        result = fn(playlist_id="pl123", strategy="nonexistent_strategy")

        assert isinstance(result, str)
        assert "**Error:**" in result
        assert "Unknown strategy" in result

    def test_fewer_than_two_tracks(self, tool_registry, mock_sp):
        mock_sp.playlist.return_value = {"name": "Single Song"}
        mock_sp.playlist_items.return_value = {
            "items": [{"track": _make_track()}],
            "next": None,
        }
        fn = tool_registry["spotify_smart_shuffle"]
        result = fn(playlist_id="pl123")

        assert isinstance(result, str)
        assert "fewer than 2 tracks" in result


# ===========================================================================
# 14. spotify_find_song (power/find_song.py)
# ===========================================================================


class TestSpotifyFindSong:

    def test_happy_path_with_title_and_artist(self, tool_registry, mock_sp):
        track = _make_track(name="Bohemian Rhapsody", artist="Queen")
        # search_with_pagination calls sp.search internally
        mock_sp.search.return_value = {
            "tracks": {"items": [track], "next": None},
        }
        fn = tool_registry["spotify_find_song"]
        result = fn(description='"Bohemian Rhapsody" by Queen')

        assert isinstance(result, str)
        assert "Parsed" in result
        assert "Bohemian Rhapsody" in result

    def test_no_results(self, tool_registry, mock_sp):
        mock_sp.search.return_value = {
            "tracks": {"items": [], "next": None},
        }
        fn = tool_registry["spotify_find_song"]
        result = fn(description="some completely random nonsense xyzzy")

        assert isinstance(result, str)
        assert "Parsed" in result
        # Should still return without crashing

    def test_spotify_exception(self, tool_registry, mock_sp):
        mock_sp.search.side_effect = _make_spotify_exception(
            429, reason="Rate Limited"
        )
        fn = tool_registry["spotify_find_song"]
        result = fn(description="any song")

        assert isinstance(result, str)
        assert "**Error:**" in result

    def test_decade_parsing(self, tool_registry, mock_sp):
        track = _make_track(name="90s Hit", artist="Old Band")
        mock_sp.search.return_value = {
            "tracks": {"items": [track], "next": None},
        }
        fn = tool_registry["spotify_find_song"]
        result = fn(description="a rock song from the 90s")

        assert isinstance(result, str)
        assert "Parsed" in result
        # Should detect year range and genre
        assert "year=" in result or "genre=" in result


# ===========================================================================
# 15. spotify_deduplicate_playlist (power/playlist_ops.py)
# ===========================================================================


class TestSpotifyDeduplicatePlaylist:

    def test_dry_run_with_duplicates(self, tool_registry, mock_sp):
        track_a = _make_track(name="Dup Song", track_id="id1", uri="spotify:track:id1")
        track_b = _make_track(name="Other Song", track_id="id2", uri="spotify:track:id2")
        items = [
            {"track": track_a},
            {"track": track_b},
            {"track": track_a},  # duplicate
        ]
        mock_sp.playlist_items.return_value = {
            "items": items,
            "next": None,
        }
        fn = tool_registry["spotify_deduplicate_playlist"]
        result = fn(playlist_id="pl123", dry_run=True)

        assert isinstance(result, str)
        assert "Duplicate Analysis" in result
        assert "Dup Song" in result
        assert "Dry run" in result
        # Should NOT have called remove
        mock_sp.playlist_remove_specific_occurrences_of_items.assert_not_called()

    def test_no_duplicates(self, tool_registry, mock_sp):
        items = [
            {"track": _make_track(name="Song A", track_id="id1", uri="spotify:track:id1")},
            {"track": _make_track(name="Song B", track_id="id2", uri="spotify:track:id2")},
        ]
        mock_sp.playlist_items.return_value = {
            "items": items,
            "next": None,
        }
        fn = tool_registry["spotify_deduplicate_playlist"]
        result = fn(playlist_id="pl123")

        assert isinstance(result, str)
        assert "No duplicates found" in result

    def test_remove_duplicates(self, tool_registry, mock_sp):
        track_a = _make_track(name="Dup Song", track_id="id1", uri="spotify:track:id1")
        track_b = _make_track(name="Other Song", track_id="id2", uri="spotify:track:id2")
        items = [
            {"track": track_a},
            {"track": track_b},
            {"track": track_a},  # duplicate at position 2
        ]
        mock_sp.playlist_items.return_value = {
            "items": items,
            "next": None,
        }
        mock_sp.playlist.return_value = {"snapshot_id": "snap123"}

        fn = tool_registry["spotify_deduplicate_playlist"]
        result = fn(playlist_id="pl123", dry_run=False)

        assert isinstance(result, str)
        assert "Removed" in result
        assert "1 duplicate" in result
        mock_sp.playlist_remove_specific_occurrences_of_items.assert_called()


# ===========================================================================
# Additional cross-cutting tests
# ===========================================================================


class TestToolReturnTypes:
    """Verify that every tool always returns a string."""

    def test_now_playing_returns_string(self, tool_registry, mock_sp):
        mock_sp.current_playback.return_value = None
        assert isinstance(tool_registry["spotify_now_playing"](), str)

    def test_play_returns_string(self, tool_registry, mock_sp):
        assert isinstance(tool_registry["spotify_play"](), str)

    def test_search_returns_string(self, tool_registry, mock_sp):
        mock_sp.search.return_value = {"tracks": {"items": [], "next": None}}
        assert isinstance(tool_registry["spotify_search"](query="test"), str)

    def test_get_my_playlists_returns_string(self, tool_registry, mock_sp):
        mock_sp.current_user_playlists.return_value = {"items": [], "total": 0}
        assert isinstance(tool_registry["spotify_get_my_playlists"](), str)

    def test_top_tracks_returns_string(self, tool_registry, mock_sp):
        mock_sp.current_user_top_tracks.return_value = {"items": []}
        assert isinstance(tool_registry["spotify_top_tracks"](), str)

    def test_get_saved_tracks_returns_string(self, tool_registry, mock_sp):
        mock_sp.current_user_saved_tracks.return_value = {"items": [], "total": 0}
        assert isinstance(tool_registry["spotify_get_saved_tracks"](), str)
