"""Hard filtering and neuroscience relevance scoring."""

from __future__ import annotations

from keywords import REJECTION_KEYWORDS, ALL_NRS_KEYWORDS
from logger import setup_logger

log = setup_logger()

NRS_THRESHOLD = 2  # Minimum NRS to keep a post


# ------------------------------------------------------------------ #
# Hard Rejection
# ------------------------------------------------------------------ #

def is_rejected(title: str, content: str | None) -> bool:
    """Return ``True`` if the post should be immediately rejected.

    Matches any rejection keyword against the combined title + content
    (case-insensitive).
    """
    text = ((title or "") + " " + (content or "")).lower()
    for keyword in REJECTION_KEYWORDS:
        if keyword in text:
            log.debug("Rejected (keyword '%s'): %s", keyword, title[:80])
            return True
    return False


# ------------------------------------------------------------------ #
# Neuroscience Relevance Score (NRS)
# ------------------------------------------------------------------ #

def calculate_nrs(title: str, content: str | None) -> int:
    """Compute the Neuroscience Relevance Score for a post.

    Scans the combined title + content for keyword matches and sums
    the associated weights.
    """
    text = ((title or "") + " " + (content or "")).lower()
    score = 0
    for keyword, weight in ALL_NRS_KEYWORDS:
        if keyword in text:
            score += weight
    return score


def passes_relevance(title: str, content: str | None) -> tuple[bool, int]:
    """Run the full filter pipeline on a single post.

    Returns
    -------
    tuple[bool, int]
        ``(passes, nrs_score)``
    """
    if is_rejected(title, content):
        return False, 0

    nrs = calculate_nrs(title, content)
    if nrs < NRS_THRESHOLD:
        log.debug("Below NRS threshold (%d < %d): %s", nrs, NRS_THRESHOLD, title[:80])
        return False, nrs

    return True, nrs
