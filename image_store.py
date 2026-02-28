"""Image store -- manages diagram file storage in data/diagrams/."""

from __future__ import annotations

import hashlib
import os

from logger import setup_logger

log = setup_logger()

_DIAGRAMS_DIR = os.path.join("data", "diagrams")


def _post_id_from_url(url: str) -> str:
    """Derive a safe filename-friendly ID from a post URL.

    Uses a short SHA-256 hash to avoid filesystem issues with
    special characters in URLs.
    """
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def ensure_diagrams_dir() -> None:
    """Create the ``data/diagrams/`` directory if it doesn't exist."""
    os.makedirs(_DIAGRAMS_DIR, exist_ok=True)


def save_diagram(url: str, image_bytes: bytes) -> str | None:
    """Save diagram image bytes to disk.

    Parameters
    ----------
    url : str
        The post URL (used to derive the filename).
    image_bytes : bytes
        Raw image data (PNG).

    Returns
    -------
    str | None
        Absolute path to the saved file, or ``None`` on failure.
    """
    ensure_diagrams_dir()

    post_id = _post_id_from_url(url)
    filename = f"{post_id}.png"
    filepath = os.path.join(_DIAGRAMS_DIR, filename)

    try:
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        log.info("Diagram saved: %s (%d bytes)", filepath, len(image_bytes))
        return os.path.abspath(filepath)
    except Exception as exc:
        log.error("Failed to save diagram %s: %s", filepath, exc)
        return None


def get_diagram_path(url: str) -> str | None:
    """Return the path to an existing diagram, or ``None`` if not found.

    Parameters
    ----------
    url : str
        The post URL.

    Returns
    -------
    str | None
        Absolute path if the file exists, otherwise ``None``.
    """
    post_id = _post_id_from_url(url)
    filepath = os.path.join(_DIAGRAMS_DIR, f"{post_id}.png")
    if os.path.isfile(filepath):
        return os.path.abspath(filepath)
    return None


def get_diagram_cid(url: str) -> str:
    """Return the MIME Content-ID for inline embedding in email.

    Parameters
    ----------
    url : str
        The post URL.

    Returns
    -------
    str
        A CID string like ``diagram_a1b2c3d4e5f6``.
    """
    post_id = _post_id_from_url(url)
    return f"diagram_{post_id}"
