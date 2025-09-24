"""Utility helpers for the anime quiz backend."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from urllib.parse import parse_qs, urlparse


_YOUTUBE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_youtube_id(value: str) -> str:
    """Extract the YouTube video ID from a URL or return it if already provided."""

    value = value.strip()
    if _YOUTUBE_ID_PATTERN.fullmatch(value):
        return value

    parsed = urlparse(value)
    if parsed.netloc.endswith("youtu.be"):
        candidate = parsed.path.lstrip("/")
        if _YOUTUBE_ID_PATTERN.fullmatch(candidate):
            return candidate
    if parsed.netloc.endswith("youtube.com"):
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            video_ids = query.get("v")
            if video_ids:
                candidate = video_ids[0]
                if _YOUTUBE_ID_PATTERN.fullmatch(candidate):
                    return candidate
        if parsed.path.startswith("/embed/"):
            candidate = parsed.path.split("/")[-1]
            if _YOUTUBE_ID_PATTERN.fullmatch(candidate):
                return candidate

    raise ValueError("Unable to determine YouTube video ID from provided value")


def compute_similarity(answer: str, guess: str) -> float:
    """Return a similarity ratio between 0 and 1 for two strings."""

    normalized_answer = _normalize_string(answer)
    normalized_guess = _normalize_string(guess)
    if not normalized_answer or not normalized_guess:
        return 0.0
    return SequenceMatcher(None, normalized_answer, normalized_guess).ratio()


def _normalize_string(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()
