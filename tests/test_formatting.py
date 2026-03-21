"""Tests for spotify_mcp/utils/formatting.py."""

from unittest.mock import patch

from spotify_mcp.utils.formatting import (
    format_track,
    format_track_list,
    format_artist,
    format_artist_list,
    ms_to_duration,
    format_album,
    format_device,
    format_playlist_summary,
)


# ---------------------------------------------------------------------------
# Helpers to build mock dicts
# ---------------------------------------------------------------------------

def _make_track(
    name="Test Song",
    artists=None,
    album_name="Test Album",
    duration_ms=210000,
):
    """Build a minimal track dict matching the Spotify API shape."""
    if artists is None:
        artists = [{"name": "Artist One"}]
    track = {
        "name": name,
        "artists": artists,
        "album": {"name": album_name},
        "duration_ms": duration_ms,
    }
    return track


def _make_artist(name="Test Artist", genres=None):
    """Build a minimal artist dict."""
    artist = {"name": name}
    if genres is not None:
        artist["genres"] = genres
    return artist


# ===========================================================================
# format_track
# ===========================================================================


class TestFormatTrack:
    """Tests for format_track()."""

    def test_basic_track(self):
        track = _make_track()
        result = format_track(track)
        assert "**Test Song**" in result
        assert "Artist One" in result
        assert "(Test Album)" in result
        # 210000 ms = 3:30
        assert "[3:30]" in result

    def test_track_with_index(self):
        track = _make_track()
        result = format_track(track, index=5)
        assert result.startswith("5. ")

    def test_track_without_index_uses_dash(self):
        track = _make_track()
        result = format_track(track)
        assert result.startswith("- ")

    def test_track_multiple_artists(self):
        track = _make_track(
            artists=[{"name": "Alice"}, {"name": "Bob"}]
        )
        result = format_track(track)
        assert "Alice, Bob" in result

    def test_track_no_album(self):
        track = _make_track()
        track["album"]["name"] = ""
        result = format_track(track)
        # Empty album name means the parenthetical should be absent
        assert "()" not in result

    def test_track_none_returns_unknown(self):
        assert format_track(None) == "_Unknown track_"

    def test_track_empty_dict_returns_unknown(self):
        # An empty dict is falsy, so format_track returns the unknown sentinel
        result = format_track({})
        assert result == "_Unknown track_"

    def test_track_duration_exactly_one_minute(self):
        track = _make_track(duration_ms=60000)
        result = format_track(track)
        assert "[1:00]" in result

    def test_track_duration_seconds_zero_padded(self):
        track = _make_track(duration_ms=65000)  # 1:05
        result = format_track(track)
        assert "[1:05]" in result


# ===========================================================================
# ms_to_duration
# ===========================================================================


class TestMsToDuration:
    """Tests for ms_to_duration()."""

    def test_zero(self):
        assert ms_to_duration(0) == "0m 0s"

    def test_one_minute(self):
        assert ms_to_duration(60000) == "1m 0s"

    def test_one_minute_thirty_seconds(self):
        assert ms_to_duration(90000) == "1m 30s"

    def test_exactly_one_hour(self):
        assert ms_to_duration(3600000) == "1h 0m"

    def test_hour_and_minutes(self):
        # 1 hour, 1 minute, 1 second = 3661000 ms
        assert ms_to_duration(3661000) == "1h 1m"

    def test_sub_second_truncated(self):
        # 999 ms -- less than 1 second
        assert ms_to_duration(999) == "0m 0s"

    def test_large_duration(self):
        # 10 hours
        assert ms_to_duration(36000000) == "10h 0m"

    def test_minutes_and_seconds_no_hours(self):
        # 5 minutes 45 seconds = 345000 ms
        assert ms_to_duration(345000) == "5m 45s"


# ===========================================================================
# format_artist
# ===========================================================================


class TestFormatArtist:
    """Tests for format_artist()."""

    def test_artist_with_genres(self):
        artist = _make_artist(genres=["rock", "indie", "alternative"])
        result = format_artist(artist)
        assert "**Test Artist**" in result
        assert "(rock, indie, alternative)" in result

    def test_artist_without_genres(self):
        artist = _make_artist(genres=[])
        result = format_artist(artist)
        assert "**Test Artist**" in result
        # No genres -- no parenthetical
        assert "(" not in result

    def test_artist_no_genres_key(self):
        artist = _make_artist()  # genres key omitted
        result = format_artist(artist)
        assert "**Test Artist**" in result
        assert "(" not in result

    def test_artist_with_index(self):
        artist = _make_artist()
        result = format_artist(artist, index=3)
        assert result.startswith("3. ")

    def test_artist_without_index_uses_dash(self):
        artist = _make_artist()
        result = format_artist(artist)
        assert result.startswith("- ")

    def test_artist_none_returns_unknown(self):
        assert format_artist(None) == "_Unknown artist_"

    def test_artist_empty_dict_returns_unknown(self):
        # An empty dict is falsy, so format_artist returns the unknown sentinel
        result = format_artist({})
        assert result == "_Unknown artist_"

    def test_artist_genres_truncated_to_three(self):
        artist = _make_artist(genres=["a", "b", "c", "d", "e"])
        result = format_artist(artist)
        # Only first 3 genres should appear
        assert "a, b, c" in result
        assert "d" not in result


# ===========================================================================
# format_track_list
# ===========================================================================


class TestFormatTrackList:
    """Tests for format_track_list()."""

    def test_empty_list(self):
        assert format_track_list([]) == "_No tracks found._"

    def test_single_track(self):
        tracks = [_make_track(name="Only One")]
        result = format_track_list(tracks)
        assert "**Only One**" in result
        assert result.startswith("1. ")

    def test_unnumbered_list(self):
        tracks = [_make_track(name="Track A")]
        result = format_track_list(tracks, numbered=False)
        assert result.startswith("- ")

    def test_multiple_tracks(self):
        tracks = [_make_track(name=f"Song {i}") for i in range(3)]
        result = format_track_list(tracks)
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert "1. " in lines[0]
        assert "2. " in lines[1]
        assert "3. " in lines[2]

    @patch("spotify_mcp.utils.formatting.MAX_DISPLAY_ITEMS", 2)
    def test_truncation_message(self):
        tracks = [_make_track(name=f"Song {i}") for i in range(5)]
        result = format_track_list(tracks)
        assert "Showing 2 of 5 tracks" in result

    def test_playlist_item_wrappers(self):
        # Playlist items wrap tracks in {"track": {...}}
        inner = _make_track(name="Wrapped")
        items = [{"track": inner}]
        result = format_track_list(items)
        assert "**Wrapped**" in result


# ===========================================================================
# format_artist_list
# ===========================================================================


class TestFormatArtistList:
    """Tests for format_artist_list()."""

    def test_empty_list(self):
        assert format_artist_list([]) == "_No artists found._"

    def test_single_artist(self):
        artists = [_make_artist(name="Solo")]
        result = format_artist_list(artists)
        assert "1. **Solo**" in result

    @patch("spotify_mcp.utils.formatting.MAX_DISPLAY_ITEMS", 2)
    def test_truncation_message(self):
        artists = [_make_artist(name=f"Artist {i}") for i in range(5)]
        result = format_artist_list(artists)
        assert "Showing 2 of 5 artists" in result


# ===========================================================================
# Miscellaneous formatters
# ===========================================================================


class TestFormatAlbum:
    """Basic tests for format_album()."""

    def test_album_none(self):
        assert format_album(None) == "_Unknown album_"

    def test_album_basic(self):
        album = {
            "name": "My Album",
            "artists": [{"name": "The Band"}],
            "release_date": "2024-06-15",
            "total_tracks": 12,
            "album_type": "album",
        }
        result = format_album(album)
        assert "**My Album**" in result
        assert "The Band" in result
        assert "2024-06-15" in result


class TestFormatDevice:
    """Basic tests for format_device()."""

    def test_active_device(self):
        device = {
            "name": "Living Room Speaker",
            "type": "Speaker",
            "is_active": True,
            "volume_percent": 75,
        }
        result = format_device(device)
        assert "Living Room Speaker" in result
        assert "(active)" in result
        assert "75%" in result

    def test_inactive_device(self):
        device = {
            "name": "Phone",
            "type": "Smartphone",
            "is_active": False,
            "volume_percent": 50,
        }
        result = format_device(device)
        assert "(active)" not in result


class TestFormatPlaylistSummary:
    """Basic tests for format_playlist_summary()."""

    def test_public_playlist(self):
        playlist = {
            "name": "Chill Vibes",
            "owner": {"display_name": "DJ Cool"},
            "tracks": {"total": 42},
            "public": True,
            "id": "abc123",
            "description": "Relaxing tunes",
        }
        result = format_playlist_summary(playlist)
        assert "**Chill Vibes** (Public)" in result
        assert "DJ Cool" in result
        assert "42 tracks" in result
        assert "_Relaxing tunes_" in result

    def test_private_playlist_no_description(self):
        playlist = {
            "name": "Secret Mix",
            "owner": {"display_name": "Me"},
            "tracks": {"total": 10},
            "public": False,
            "id": "xyz789",
        }
        result = format_playlist_summary(playlist)
        assert "(Private)" in result
