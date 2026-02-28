"""Data models for the NeuroAI Digest pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any

from hashing import generate_hash


@dataclass
class Post:
    """Represents a single research item collected from an RSS feed.

    Attributes
    ----------
    title : str
        Title of the article / post.
    url : str
        Canonical URL (used as the unique key).
    source : str
        Human-readable feed name (e.g. ``"arXiv q-bio.NC"``).
    published : str
        ISO-formatted publication timestamp.
    content_hash : str
        SHA-256 hash of ``title + url`` for cross-feed dedup.
    """

    title: str
    url: str
    source: str
    published: str
    content_hash: str = field(default="", repr=False)

    # ------------------------------------------------------------------ #
    # Factory
    # ------------------------------------------------------------------ #
    @classmethod
    def from_feed_entry(cls, entry: Any, source_name: str) -> Post | None:
        """Convert a ``feedparser`` entry dict into a :class:`Post`.

        Returns ``None`` when the entry lacks both *title* and *link*,
        making it impossible to create a meaningful record.
        """
        title = (getattr(entry, "title", None) or "").strip()
        url = (getattr(entry, "link", None) or "").strip()

        # Both are required for a usable record
        if not title and not url:
            return None

        # Provide sensible fallbacks
        if not title:
            title = "(untitled)"
        if not url:
            return None  # URL is our unique key — cannot skip it

        # Published date: try several common feedparser fields
        published_raw = (
            getattr(entry, "published", None)
            or getattr(entry, "updated", None)
            or None
        )
        if published_raw:
            published = str(published_raw).strip()
        else:
            published = datetime.now(timezone.utc).isoformat()

        content_hash = generate_hash(title, url)

        return cls(
            title=title,
            url=url,
            source=source_name,
            published=published,
            content_hash=content_hash,
        )
