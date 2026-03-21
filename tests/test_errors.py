"""Tests for spotify_mcp/utils/errors.py."""

import pytest
from unittest.mock import MagicMock

from spotipy.exceptions import SpotifyException

from spotify_mcp.utils.errors import handle_spotify_error, catch_spotify_errors


# ---------------------------------------------------------------------------
# Helpers to build mock SpotifyExceptions
# ---------------------------------------------------------------------------

def _make_spotify_exception(http_status, reason="", msg="", headers=None):
    """Create a real SpotifyException with the given attributes.

    SpotifyException.__init__ signature: (self, http_status, -1, msg, reason, headers)
    """
    exc = SpotifyException(http_status, -1, msg, reason=reason, headers=headers)
    return exc


# ===========================================================================
# handle_spotify_error
# ===========================================================================


class TestHandleSpotifyError:
    """Tests for handle_spotify_error()."""

    def test_404_not_found(self):
        exc = _make_spotify_exception(404, reason="Not Found")
        result = handle_spotify_error(exc)
        assert "**Error:**" in result
        assert "not found" in result.lower()

    def test_429_rate_limited_no_headers(self):
        exc = _make_spotify_exception(429, reason="Rate Limited")
        result = handle_spotify_error(exc)
        assert "**Error:**" in result
        assert "Rate limited" in result

    def test_429_rate_limited_with_retry_after(self):
        exc = _make_spotify_exception(
            429, reason="Rate Limited", headers={"Retry-After": "30"}
        )
        result = handle_spotify_error(exc)
        assert "30 seconds" in result

    def test_401_auth_expired(self):
        exc = _make_spotify_exception(401, reason="Unauthorized")
        result = handle_spotify_error(exc)
        assert "**Error:**" in result
        assert "Authorization expired" in result or "authorization" in result.lower()

    def test_403_premium_required(self):
        exc = _make_spotify_exception(403, reason="Forbidden")
        result = handle_spotify_error(exc)
        assert "**Error:**" in result
        assert "Premium" in result

    def test_no_active_device_message(self):
        exc = _make_spotify_exception(
            403, msg="Player command failed: No active device found"
        )
        # The msg passed to SpotifyException ends up in str(e)
        result = handle_spotify_error(exc)
        assert "**Error:**" in result
        # Should match the NO_ACTIVE_DEVICE branch or the 403 branch
        assert "device" in result.lower() or "Premium" in result

    def test_generic_error_with_reason(self):
        exc = _make_spotify_exception(500, reason="Internal Server Error")
        result = handle_spotify_error(exc)
        assert "**Error:**" in result
        assert "Internal Server Error" in result

    def test_generic_error_without_reason(self):
        exc = _make_spotify_exception(502, msg="Bad Gateway")
        result = handle_spotify_error(exc)
        assert "**Error:**" in result


# ===========================================================================
# catch_spotify_errors decorator
# ===========================================================================


class TestCatchSpotifyErrors:
    """Tests for the catch_spotify_errors decorator."""

    def test_passes_through_normal_return(self):
        @catch_spotify_errors
        def happy_path():
            return "all good"

        assert happy_path() == "all good"

    def test_catches_spotify_exception(self):
        @catch_spotify_errors
        def raises_spotify():
            raise SpotifyException(404, -1, "Not found")

        result = raises_spotify()
        assert "**Error:**" in result
        assert "not found" in result.lower()

    def test_catches_value_error(self):
        @catch_spotify_errors
        def raises_value():
            raise ValueError("bad input")

        result = raises_value()
        assert result == "**Error:** bad input"

    def test_preserves_function_name(self):
        @catch_spotify_errors
        def my_function():
            """Docstring."""
            return "ok"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "Docstring."

    def test_passes_args_and_kwargs(self):
        @catch_spotify_errors
        def add(a, b, extra=0):
            return a + b + extra

        assert add(1, 2, extra=3) == 6

    def test_does_not_catch_other_exceptions(self):
        @catch_spotify_errors
        def raises_type_error():
            raise TypeError("nope")

        with pytest.raises(TypeError, match="nope"):
            raises_type_error()

    def test_spotify_exception_429_through_decorator(self):
        @catch_spotify_errors
        def rate_limited():
            raise SpotifyException(
                429, -1, "Too Many Requests",
                headers={"Retry-After": "10"},
            )

        result = rate_limited()
        assert "Rate limited" in result

    def test_spotify_exception_401_through_decorator(self):
        @catch_spotify_errors
        def auth_expired():
            raise SpotifyException(401, -1, "Token expired")

        result = auth_expired()
        assert "Authorization expired" in result or "authorization" in result.lower()
