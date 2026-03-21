"""Tests for spotify_mcp/utils/uri_parser.py."""

import pytest

from spotify_mcp.utils.uri_parser import parse_spotify_id, VALID_TYPES


# ---------------------------------------------------------------------------
# Fixtures / constants
# ---------------------------------------------------------------------------

# A valid 22-character alphanumeric Spotify ID
VALID_ID = "6rqhFgbbKwnb9MLmUQDhG6"  # exactly 22 chars


class TestParseSpotifyIdWithURI:
    """Test parse_spotify_id when given spotify:{type}:{id} URIs."""

    def test_valid_track_uri(self):
        result = parse_spotify_id(f"spotify:track:{VALID_ID}")
        assert result == VALID_ID

    def test_valid_album_uri(self):
        result = parse_spotify_id(f"spotify:album:{VALID_ID}")
        assert result == VALID_ID

    def test_valid_artist_uri(self):
        result = parse_spotify_id(f"spotify:artist:{VALID_ID}")
        assert result == VALID_ID

    def test_valid_playlist_uri(self):
        result = parse_spotify_id(f"spotify:playlist:{VALID_ID}")
        assert result == VALID_ID

    def test_valid_show_uri(self):
        result = parse_spotify_id(f"spotify:show:{VALID_ID}")
        assert result == VALID_ID

    def test_valid_episode_uri(self):
        result = parse_spotify_id(f"spotify:episode:{VALID_ID}")
        assert result == VALID_ID

    def test_uri_with_leading_trailing_whitespace(self):
        result = parse_spotify_id(f"  spotify:track:{VALID_ID}  ")
        assert result == VALID_ID

    def test_uri_with_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported Spotify type"):
            parse_spotify_id(f"spotify:bogus:{VALID_ID}")


class TestParseSpotifyIdWithURL:
    """Test parse_spotify_id when given https://open.spotify.com/{type}/{id} URLs."""

    def test_valid_track_url(self):
        url = f"https://open.spotify.com/track/{VALID_ID}"
        assert parse_spotify_id(url) == VALID_ID

    def test_valid_album_url(self):
        url = f"https://open.spotify.com/album/{VALID_ID}"
        assert parse_spotify_id(url) == VALID_ID

    def test_url_with_query_params(self):
        url = f"https://open.spotify.com/track/{VALID_ID}?si=abc123"
        assert parse_spotify_id(url) == VALID_ID

    def test_http_url_also_works(self):
        url = f"http://open.spotify.com/track/{VALID_ID}"
        assert parse_spotify_id(url) == VALID_ID

    def test_url_with_unsupported_type_raises(self):
        url = f"https://open.spotify.com/bogus/{VALID_ID}"
        with pytest.raises(ValueError, match="Unsupported Spotify type"):
            parse_spotify_id(url)


class TestParseSpotifyIdWithBareID:
    """Test parse_spotify_id when given a bare 22-character alphanumeric ID."""

    def test_bare_id(self):
        assert parse_spotify_id(VALID_ID) == VALID_ID

    def test_bare_id_all_digits(self):
        bare = "1234567890123456789012"
        assert parse_spotify_id(bare) == bare

    def test_bare_id_all_alpha(self):
        bare = "abcdefghijklmnopqrstuv"
        assert parse_spotify_id(bare) == bare

    def test_bare_id_mixed_case(self):
        bare = "AbCdEfGhIjKlMnOpQrStUv"
        assert parse_spotify_id(bare) == bare

    def test_bare_id_with_whitespace_stripped(self):
        assert parse_spotify_id(f"  {VALID_ID}  ") == VALID_ID


class TestExpectedTypeValidation:
    """Test the expected_type parameter."""

    def test_expected_type_matches_uri(self):
        result = parse_spotify_id(
            f"spotify:track:{VALID_ID}", expected_type="track"
        )
        assert result == VALID_ID

    def test_expected_type_matches_url(self):
        url = f"https://open.spotify.com/album/{VALID_ID}"
        result = parse_spotify_id(url, expected_type="album")
        assert result == VALID_ID

    def test_expected_type_none_allows_any(self):
        # No expected_type -- should accept any valid type
        assert parse_spotify_id(f"spotify:artist:{VALID_ID}") == VALID_ID

    def test_bare_id_ignores_expected_type(self):
        # Bare IDs have no parsed type, so expected_type cannot be checked
        # The function simply returns the bare ID
        result = parse_spotify_id(VALID_ID, expected_type="track")
        assert result == VALID_ID


class TestTypeMismatchRaises:
    """Test that type mismatches raise ValueError."""

    def test_uri_type_mismatch(self):
        with pytest.raises(ValueError, match="Expected type 'album' but got 'track'"):
            parse_spotify_id(f"spotify:track:{VALID_ID}", expected_type="album")

    def test_url_type_mismatch(self):
        url = f"https://open.spotify.com/track/{VALID_ID}"
        with pytest.raises(ValueError, match="Expected type 'playlist' but got 'track'"):
            parse_spotify_id(url, expected_type="playlist")


class TestInvalidInputRaises:
    """Test that invalid inputs raise ValueError."""

    def test_invalid_expected_type_string(self):
        with pytest.raises(ValueError, match="Invalid expected_type"):
            parse_spotify_id(VALID_ID, expected_type="song")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Cannot parse Spotify ID"):
            parse_spotify_id("")

    def test_random_text(self):
        with pytest.raises(ValueError, match="Cannot parse Spotify ID"):
            parse_spotify_id("not-a-spotify-id-at-all")

    def test_id_too_short(self):
        with pytest.raises(ValueError, match="Cannot parse Spotify ID"):
            parse_spotify_id("abc123")

    def test_id_too_long(self):
        with pytest.raises(ValueError, match="Cannot parse Spotify ID"):
            parse_spotify_id("A" * 23)

    def test_id_with_special_chars(self):
        with pytest.raises(ValueError, match="Cannot parse Spotify ID"):
            parse_spotify_id("abcdefghijklmnopqrst!@")

    def test_malformed_uri(self):
        with pytest.raises(ValueError, match="Cannot parse Spotify ID"):
            parse_spotify_id("spotify:track:")

    def test_malformed_url(self):
        with pytest.raises(ValueError, match="Cannot parse Spotify ID"):
            parse_spotify_id("https://open.spotify.com/track/")


class TestValidTypesConstant:
    """Sanity checks on the VALID_TYPES set."""

    def test_contains_core_types(self):
        expected = {"track", "album", "artist", "playlist", "show", "episode"}
        assert VALID_TYPES == expected
