"""Pure regex utility for parsing Spotify URIs, URLs, and bare IDs."""

import logging
import re

logger = logging.getLogger(__name__)

VALID_TYPES = {"track", "album", "artist", "playlist", "show", "episode"}

_URI_RE = re.compile(
    r"^spotify:(?P<type>[a-z]+):(?P<id>[A-Za-z0-9]{22})$"
)

_URL_RE = re.compile(
    r"^https?://open\.spotify\.com/(?P<type>[a-z]+)/(?P<id>[A-Za-z0-9]{22})(?:\?.*)?$"
)

_BARE_ID_RE = re.compile(
    r"^[A-Za-z0-9]{22}$"
)


def parse_spotify_id(input_str: str, expected_type: str | None = None) -> str:
    """Extract a Spotify ID from a URI, URL, or bare ID string.

    Args:
        input_str: A Spotify URI (spotify:track:abc123...),
                   URL (https://open.spotify.com/track/abc123...),
                   or bare 22-character alphanumeric ID.
        expected_type: If provided, validates the parsed type matches.
                       Must be one of: track, album, artist, playlist, show, episode.

    Returns:
        The 22-character Spotify ID.

    Raises:
        ValueError: If the input cannot be parsed or the type does not match.
    """
    if expected_type is not None and expected_type not in VALID_TYPES:
        raise ValueError(
            f"Invalid expected_type '{expected_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_TYPES))}"
        )

    input_str = input_str.strip()

    # Try spotify:{type}:{id} URI
    m = _URI_RE.match(input_str)
    if m:
        parsed_type = m.group("type")
        parsed_id = m.group("id")
        if parsed_type not in VALID_TYPES:
            raise ValueError(
                f"Unsupported Spotify type '{parsed_type}' in URI. "
                f"Must be one of: {', '.join(sorted(VALID_TYPES))}"
            )
        if expected_type and parsed_type != expected_type:
            raise ValueError(
                f"Expected type '{expected_type}' but got '{parsed_type}' from URI"
            )
        logger.debug("Parsed URI: type=%s id=%s", parsed_type, parsed_id)
        return parsed_id

    # Try https://open.spotify.com/{type}/{id} URL
    m = _URL_RE.match(input_str)
    if m:
        parsed_type = m.group("type")
        parsed_id = m.group("id")
        if parsed_type not in VALID_TYPES:
            raise ValueError(
                f"Unsupported Spotify type '{parsed_type}' in URL. "
                f"Must be one of: {', '.join(sorted(VALID_TYPES))}"
            )
        if expected_type and parsed_type != expected_type:
            raise ValueError(
                f"Expected type '{expected_type}' but got '{parsed_type}' from URL"
            )
        logger.debug("Parsed URL: type=%s id=%s", parsed_type, parsed_id)
        return parsed_id

    # Try bare 22-character alphanumeric ID
    m = _BARE_ID_RE.match(input_str)
    if m:
        logger.debug("Parsed bare ID: %s", input_str)
        return input_str

    raise ValueError(
        f"Cannot parse Spotify ID from '{input_str}'. "
        "Expected a Spotify URI (spotify:type:id), "
        "URL (https://open.spotify.com/type/id), "
        "or a 22-character alphanumeric ID."
    )
