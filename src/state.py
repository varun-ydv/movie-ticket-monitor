"""State management — track what we've already notified about."""

import json
import os
from src.config import STATE_FILE


def _ensure_state_file():
    """Create the state file and directories if they don't exist."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({}, f)


def load_state() -> dict:
    """Load seen state from disk. Returns {key: timestamp} dict."""
    _ensure_state_file()
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_state(state: dict):
    """Persist state to disk."""
    _ensure_state_file()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def make_key(cinema_id: str, movie_title: str, status: str) -> str:
    """Create a unique dedup key like 'hoyts_the-odyssey_tickets_available'."""
    slug = movie_title.lower().replace(" ", "-").replace(":", "")
    return f"{cinema_id}_{slug}_{status}"


def is_new(state: dict, key: str) -> bool:
    """Check if this key has been seen before."""
    return key not in state


def mark_seen(state: dict, key: str):
    """Mark a key as seen with current timestamp."""
    from datetime import datetime, timezone
    state[key] = datetime.now(timezone.utc).isoformat()
