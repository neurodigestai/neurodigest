"""Digest builder -- assembles ranked, summarized posts into an HTML digest."""

from __future__ import annotations

from typing import List

from html_template import render_digest
from categories import MAJOR_RESEARCH, UNDERSTANDING, COMMUNITY, TOOLS
from image_store import get_diagram_path, get_diagram_cid
from config_loader import Config
from logger import setup_logger

log = setup_logger()

# Ordered section names for the digest
_SECTION_ORDER = [
    MAJOR_RESEARCH,
    UNDERSTANDING,
    COMMUNITY,
    TOOLS,
]

MAX_DIGEST_ITEMS = 20


def build_digest(selected_posts: list) -> tuple[str | None, list[dict]]:
    """Build an HTML digest from ranked posts that have summaries.

    Parameters
    ----------
    selected_posts : list
        List of ``RankedPost`` objects (from the ranker module).
        Each must have: ``title``, ``url``, ``source``, ``category``,
        and a summary must exist in the database.

    Returns
    -------
    tuple[str | None, list[dict]]
        ``(html_string, diagram_attachments)``
        - ``html_string``: Complete HTML, or ``None`` if no summarized posts.
        - ``diagram_attachments``: List of dicts with ``path`` and ``cid``
          keys for inline image attachment in the email.
    """
    from database import get_post_summary  # avoid circular import

    # Collect posts that have valid summaries
    items_by_category: dict[str, list[dict]] = {}
    diagram_attachments: list[dict] = []
    total_items = 0

    for rp in selected_posts:
        if total_items >= MAX_DIGEST_ITEMS:
            break

        summary = get_post_summary(rp.url)
        if not summary or summary == "SUMMARY_FAILED":
            continue

        item = {
            "title": rp.title,
            "url": rp.url,
            "source": rp.source,
            "summary": summary,
            "diagram_cid": None,
        }

        # Check for diagram (Major Research items only)
        if rp.category == MAJOR_RESEARCH:
            diagram_path = get_diagram_path(rp.url)
            if diagram_path:
                cid = get_diagram_cid(rp.url)
                item["diagram_cid"] = cid
                diagram_attachments.append({
                    "path": diagram_path,
                    "cid": cid,
                })
                log.debug("Diagram attached for: %s", rp.title[:60])

        category = rp.category
        items_by_category.setdefault(category, []).append(item)
        total_items += 1

    if total_items == 0:
        log.warning("No summarized posts available for digest")
        return None, []

    # Build ordered sections (only include non-empty categories)
    ordered_sections: dict[str, list[dict]] = {}
    for section_name in _SECTION_ORDER:
        if section_name in items_by_category:
            ordered_sections[section_name] = items_by_category[section_name]

    # Include any categories not in the predefined order
    for category, items in items_by_category.items():
        if category not in ordered_sections:
            ordered_sections[category] = items

    digest_title = Config.DIGEST_TITLE
    html = render_digest(digest_title, ordered_sections)

    log.info("Digest created with %d items across %d sections",
             total_items, len(ordered_sections))

    return html, diagram_attachments
