import os
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
SPOTIFY_CACHE_DIR = os.getenv("SPOTIFY_CACHE_DIR", os.path.dirname(os.path.abspath(__file__)))

SCOPES = " ".join([
    # Playback
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    # History & Personalization
    "user-read-recently-played",
    "user-top-read",
    # Library
    "user-library-read",
    "user-library-modify",
    # Shows/Podcasts
    "user-read-playback-position",
    # Playlists
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    # Follow
    "user-follow-read",
    "user-follow-modify",
])

# Pagination defaults
DEFAULT_LIMIT = 20
MAX_SEARCH_PAGE = 10  # Spotify Feb 2026: max 10 per search page
MAX_PLAYLIST_PAGE = 100  # Max items per playlist page
MAX_DISPLAY_ITEMS = 50  # Cap output lists for readability

# Mood-to-genre mapping for discovery without recommendations API
MOOD_GENRE_MAP = {
    "happy": ["pop", "dance", "funk", "disco"],
    "sad": ["indie", "folk", "singer-songwriter", "blues"],
    "energetic": ["edm", "drum-and-bass", "punk", "metal", "workout"],
    "chill": ["ambient", "lo-fi", "chillwave", "jazz", "bossa-nova"],
    "focused": ["classical", "ambient", "study", "piano"],
    "romantic": ["r-n-b", "soul", "jazz", "latin"],
    "angry": ["metal", "hardcore", "punk", "industrial"],
    "party": ["edm", "hip-hop", "reggaeton", "dance", "house"],
}

DECADE_RANGES = {
    "1960s": "1960-1969", "1970s": "1970-1979", "1980s": "1980-1989",
    "1990s": "1990-1999", "2000s": "2000-2009", "2010s": "2010-2019",
    "2020s": "2020-2029",
}

GENRE_CLUSTERS = {
    "rock": ["rock", "punk", "grunge", "metal", "emo", "post-punk", "garage"],
    "electronic": ["electronic", "edm", "house", "techno", "ambient", "synth", "chillwave", "drum-and-bass"],
    "hip-hop": ["hip hop", "hip-hop", "rap", "trap"],
    "pop": ["pop", "dance pop", "indie pop", "synth-pop"],
    "r&b/soul": ["r&b", "r-n-b", "soul", "funk", "neo soul"],
    "jazz": ["jazz", "bossa", "swing", "bossa-nova"],
    "classical": ["classical", "piano", "orchestral", "opera"],
    "folk/country": ["folk", "country", "bluegrass", "singer-songwriter"],
    "latin": ["latin", "reggaeton", "salsa"],
}

GENRE_ENERGY_ESTIMATE = {
    "metal": 0.95, "hardcore": 0.95, "drum-and-bass": 0.92,
    "punk": 0.9, "edm": 0.9, "industrial": 0.88, "workout": 0.85,
    "house": 0.82, "dance": 0.8, "reggaeton": 0.78,
    "hip-hop": 0.75, "funk": 0.72, "rock": 0.7,
    "pop": 0.65, "r-n-b": 0.55, "indie": 0.5, "soul": 0.5,
    "blues": 0.45, "jazz": 0.4, "folk": 0.35,
    "singer-songwriter": 0.3, "bossa-nova": 0.3,
    "classical": 0.25, "chillwave": 0.25, "piano": 0.2, "lo-fi": 0.2,
    "ambient": 0.15,
}
