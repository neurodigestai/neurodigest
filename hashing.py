"""Content hashing for duplicate detection across feeds."""

import hashlib


def generate_hash(title: str, url: str) -> str:
    """Return a SHA-256 hex digest of *title* + *url*.

    This allows detection of the same article appearing in multiple
    RSS sources.
    """
    raw = (title + url).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
