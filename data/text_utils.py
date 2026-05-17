"""Text-normalization helpers for tolerant SIGAM searches."""

from __future__ import annotations

import re
import unicodedata


def normalize_search_text(value: str | None) -> str:
    """Normalize text for accent-insensitive and punctuation-tolerant search.

    Args:
        value: Source text to normalize.

    Returns:
        Lowercase normalized text with punctuation removed and spaces collapsed.
    """

    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    cleaned = re.sub(r"[^0-9A-Za-z]+", " ", without_marks)
    collapsed = re.sub(r"\s+", " ", cleaned).strip().lower()
    return collapsed.replace(" ", "")


def normalized_contains(value: str | None, query: str | None) -> bool:
    """Return whether normalized text contains a normalized query.

    Args:
        value: Source text to inspect.
        query: Search query to compare.

    Returns:
        ``True`` when the normalized query is contained in the normalized value.
    """

    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return True
    return normalized_query in normalize_search_text(value)
