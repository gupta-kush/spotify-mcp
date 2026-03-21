"""Tests for spotify_mcp/utils/helpers.py."""

import pytest

from spotify_mcp.utils.helpers import chunked, get_primary_artist


# ===========================================================================
# chunked
# ===========================================================================


class TestChunked:
    """Tests for chunked()."""

    def test_even_split(self):
        result = list(chunked([1, 2, 3, 4], 2))
        assert result == [[1, 2], [3, 4]]

    def test_uneven_split(self):
        result = list(chunked([1, 2, 3, 4, 5], 2))
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunk_size_larger_than_list(self):
        result = list(chunked([1, 2], 10))
        assert result == [[1, 2]]

    def test_chunk_size_equals_list_length(self):
        result = list(chunked([1, 2, 3], 3))
        assert result == [[1, 2, 3]]

    def test_chunk_size_one(self):
        result = list(chunked([1, 2, 3], 1))
        assert result == [[1], [2], [3]]

    def test_empty_list(self):
        result = list(chunked([], 5))
        assert result == []

    def test_single_element(self):
        result = list(chunked([42], 3))
        assert result == [[42]]

    def test_returns_generator(self):
        gen = chunked([1, 2, 3], 2)
        # Should be a generator, not a list
        assert hasattr(gen, "__next__")

    def test_large_chunk_size_100(self):
        items = list(range(250))
        chunks = list(chunked(items, 100))
        assert len(chunks) == 3
        assert len(chunks[0]) == 100
        assert len(chunks[1]) == 100
        assert len(chunks[2]) == 50

    def test_strings_work(self):
        result = list(chunked(["a", "b", "c", "d"], 3))
        assert result == [["a", "b", "c"], ["d"]]


# ===========================================================================
# get_primary_artist
# ===========================================================================


class TestGetPrimaryArtist:
    """Tests for get_primary_artist()."""

    def test_normal_track(self):
        track = {
            "artists": [
                {"name": "Taylor Swift"},
                {"name": "Ed Sheeran"},
            ]
        }
        assert get_primary_artist(track) == "Taylor Swift"

    def test_single_artist(self):
        track = {"artists": [{"name": "Adele"}]}
        assert get_primary_artist(track) == "Adele"

    def test_empty_artists_list(self):
        track = {"artists": []}
        assert get_primary_artist(track) == "Unknown"

    def test_missing_artists_key(self):
        track = {"name": "Orphan Song"}
        assert get_primary_artist(track) == "Unknown"

    def test_empty_dict(self):
        assert get_primary_artist({}) == "Unknown"

    def test_artist_missing_name_key(self):
        track = {"artists": [{"id": "abc"}]}
        assert get_primary_artist(track) == "Unknown"

    def test_first_artist_selected(self):
        # Verify it always picks index 0
        track = {
            "artists": [
                {"name": "First"},
                {"name": "Second"},
                {"name": "Third"},
            ]
        }
        assert get_primary_artist(track) == "First"
