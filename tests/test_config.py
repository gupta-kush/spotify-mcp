"""Tests for spotify_mcp/config.py -- configuration constants and mappings."""

import pytest

from spotify_mcp.config import (
    MOOD_GENRE_MAP,
    DECADE_RANGES,
    GENRE_ENERGY_ESTIMATE,
    GENRE_CLUSTERS,
    DEFAULT_LIMIT,
    MAX_SEARCH_PAGE,
    MAX_PLAYLIST_PAGE,
    MAX_DISPLAY_ITEMS,
    SESSION_GAP_SECONDS,
    API_BATCH_INTERVAL,
    API_SLEEP_SECONDS,
    DESCRIPTION_MAX_LENGTH,
    ARTIST_SAMPLE_SIZE,
    MAX_RELATED_ARTISTS,
    SCOPES,
)


# ===========================================================================
# MOOD_GENRE_MAP
# ===========================================================================


class TestMoodGenreMap:
    """Tests for MOOD_GENRE_MAP configuration."""

    EXPECTED_MOODS = {
        "happy", "sad", "energetic", "chill",
        "focused", "romantic", "angry", "party",
    }

    def test_has_expected_keys(self):
        assert set(MOOD_GENRE_MAP.keys()) == self.EXPECTED_MOODS

    def test_values_are_non_empty_lists(self):
        for mood, genres in MOOD_GENRE_MAP.items():
            assert isinstance(genres, list), f"{mood} value is not a list"
            assert len(genres) > 0, f"{mood} has an empty genre list"

    def test_all_genres_are_strings(self):
        for mood, genres in MOOD_GENRE_MAP.items():
            for genre in genres:
                assert isinstance(genre, str), (
                    f"{mood} contains non-string genre: {genre!r}"
                )


# ===========================================================================
# DECADE_RANGES
# ===========================================================================


class TestDecadeRanges:
    """Tests for DECADE_RANGES configuration."""

    EXPECTED_DECADES = {"1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"}

    def test_has_expected_keys(self):
        assert set(DECADE_RANGES.keys()) == self.EXPECTED_DECADES

    def test_values_are_year_ranges(self):
        for decade, year_range in DECADE_RANGES.items():
            assert isinstance(year_range, str), f"{decade} value not a string"
            parts = year_range.split("-")
            assert len(parts) == 2, f"{decade} range not in 'YYYY-YYYY' format"
            start, end = int(parts[0]), int(parts[1])
            assert 1900 <= start <= 2100, f"{decade} start year out of range"
            assert end - start == 9, f"{decade} range does not span exactly 9 years"


# ===========================================================================
# GENRE_ENERGY_ESTIMATE
# ===========================================================================


class TestGenreEnergyEstimate:
    """Tests for GENRE_ENERGY_ESTIMATE configuration."""

    def test_all_values_between_0_and_1(self):
        for genre, energy in GENRE_ENERGY_ESTIMATE.items():
            assert 0.0 <= energy <= 1.0, (
                f"Genre '{genre}' has energy {energy} outside [0, 1]"
            )

    def test_not_empty(self):
        assert len(GENRE_ENERGY_ESTIMATE) > 0

    def test_all_keys_are_strings(self):
        for genre in GENRE_ENERGY_ESTIMATE:
            assert isinstance(genre, str)

    def test_high_energy_genres(self):
        # Metal and hardcore should be among the highest
        assert GENRE_ENERGY_ESTIMATE.get("metal", 0) >= 0.9
        assert GENRE_ENERGY_ESTIMATE.get("hardcore", 0) >= 0.9

    def test_low_energy_genres(self):
        # Ambient should be among the lowest
        assert GENRE_ENERGY_ESTIMATE.get("ambient", 1) <= 0.2


# ===========================================================================
# GENRE_CLUSTERS
# ===========================================================================


class TestGenreClusters:
    """Tests for GENRE_CLUSTERS configuration."""

    def test_has_common_cluster_keys(self):
        expected_clusters = {"rock", "electronic", "hip-hop", "pop", "jazz", "classical"}
        assert expected_clusters.issubset(set(GENRE_CLUSTERS.keys()))

    def test_values_are_non_empty_lists(self):
        for cluster, genres in GENRE_CLUSTERS.items():
            assert isinstance(genres, list), f"{cluster} value is not a list"
            assert len(genres) > 0, f"{cluster} has empty genre list"


# ===========================================================================
# Numeric constants
# ===========================================================================


class TestNumericConstants:
    """Tests for numeric configuration constants."""

    def test_session_gap_positive(self):
        assert SESSION_GAP_SECONDS > 0

    def test_session_gap_is_reasonable(self):
        # Should be at least a few minutes, at most a few hours
        assert 60 <= SESSION_GAP_SECONDS <= 7200

    def test_default_limit_positive(self):
        assert DEFAULT_LIMIT > 0

    def test_max_search_page_positive(self):
        assert MAX_SEARCH_PAGE > 0

    def test_max_search_page_at_most_50(self):
        # Spotify Feb 2026 constraint: max 10 per search page
        assert MAX_SEARCH_PAGE <= 50

    def test_max_playlist_page_positive(self):
        assert MAX_PLAYLIST_PAGE > 0

    def test_max_display_items_positive(self):
        assert MAX_DISPLAY_ITEMS > 0

    def test_api_batch_interval_positive(self):
        assert API_BATCH_INTERVAL > 0

    def test_api_sleep_seconds_non_negative(self):
        assert API_SLEEP_SECONDS >= 0

    def test_description_max_length_positive(self):
        assert DESCRIPTION_MAX_LENGTH > 0

    def test_artist_sample_size_positive(self):
        assert ARTIST_SAMPLE_SIZE > 0

    def test_max_related_artists_positive(self):
        assert MAX_RELATED_ARTISTS > 0


# ===========================================================================
# SCOPES
# ===========================================================================


class TestScopes:
    """Tests for the Spotify OAuth SCOPES string."""

    def test_scopes_is_string(self):
        assert isinstance(SCOPES, str)

    def test_scopes_non_empty(self):
        assert len(SCOPES) > 0

    def test_contains_playback_scopes(self):
        assert "user-read-playback-state" in SCOPES
        assert "user-modify-playback-state" in SCOPES

    def test_contains_library_scopes(self):
        assert "user-library-read" in SCOPES
        assert "user-library-modify" in SCOPES

    def test_contains_playlist_scopes(self):
        assert "playlist-read-private" in SCOPES
        assert "playlist-modify-public" in SCOPES
