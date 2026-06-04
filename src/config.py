"""Configuration — target movies, cinemas, and environment variables."""

import os
from pathlib import Path

# Load .env file for local development (GitHub Actions uses secrets instead)
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

# Movies to watch for. Each has a canonical title and strict match phrases.
# Use specific multi-word phrases to avoid false positives (e.g. "avengers"
# alone would match "Avengers: Endgame Re-Release" which is NOT our target).
MOVIES = [
    {
        "title": "The Odyssey",
        "aliases": ["the odyssey"],
        "release": "July 17, 2026",
    },
    {
        "title": "Supergirl: Woman of Tomorrow",
        "aliases": ["supergirl"],
        "release": "June 26, 2026",
    },
    {
        "title": "Spider-Man: Brand New Day",
        "aliases": ["brand new day"],
        "release": "July 31, 2026",
    },
    {
        "title": "Avengers: Doomsday",
        "aliases": ["doomsday", "avengers doomsday"],
        "release": "December 18, 2026",
    },
]

# Cinema sites to scrape.
CINEMAS = {
    "dendy": {
        "name": "Dendy Canberra",
        "coming_soon_url": "https://canberra.dendy.com.au/coming-soon/",
        "now_showing_url": "https://canberra.dendy.com.au/home-page/",
    },
    "hoyts": {
        "name": "Hoyts",
        "coming_soon_url": "https://www.hoyts.com.au/movies/coming-soon",
        "now_showing_url": "https://www.hoyts.com.au/Movies",
    },
    "event": {
        "name": "Event Cinemas Sydney IMAX",
        "coming_soon_url": "https://www.eventcinemas.com.au/Movies/ComingSoon",
        "now_showing_url": "https://www.eventcinemas.com.au/Movies",
    },
}

# Telegram configuration (set via environment variables).
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# State file path (relative to project root).
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "state", "seen.json")
