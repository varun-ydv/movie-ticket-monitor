"""Movie title matching against our target list."""

import re
from src.config import MOVIES


def normalize(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    t = title.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def match_movie(raw_title: str) -> dict | None:
    """Return the matched movie dict if raw_title matches any target, else None.

    Matching strategy: normalise both sides, then check if ANY alias is a
    substring of the normalised title. Aliases are specific multi-word phrases
    to avoid false positives (e.g. "brand new day" not just "spider-man").
    """
    normalized = normalize(raw_title)

    for movie in MOVIES:
        for alias in movie["aliases"]:
            if normalize(alias) in normalized:
                return movie

    return None
