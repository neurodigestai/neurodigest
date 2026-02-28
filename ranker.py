"""Ranking, popularity boost, deduplication and top-N selection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict

from filter_engine import passes_relevance
from categories import get_source_weight, get_source_priority, assign_category
from logger import setup_logger

log = setup_logger()

TOP_N = 20  # Maximum items to send to the digest


# ------------------------------------------------------------------ #
# Ranked Post container
# ------------------------------------------------------------------ #

@dataclass
class RankedPost:
    """A post enriched with scoring and category metadata."""

    title: str
    url: str
    source: str
    content: str | None
    nrs: int = 0
    source_weight: int = 0
    popularity_bonus: int = 0
    final_score: int = 0
    category: str = ""

    @property
    def dedup_key(self) -> str:
        """Normalised key for cross-source deduplication.

        Uses the first 60 lower-cased alphanumeric characters of the
        title so that slight wording differences still match.
        """
        norm = re.sub(r"[^a-z0-9]", "", self.title.lower())
        return norm[:60]


# ------------------------------------------------------------------ #
# Popularity Boost
# ------------------------------------------------------------------ #

def _popularity_bonus(post: RankedPost) -> int:
    """Apply source-specific popularity bonuses."""
    bonus = 0
    title_lower = (post.title or "").lower()
    content_lower = (post.content or "").lower()
    combined = title_lower + " " + content_lower

    # Reddit: look for upvote signals (feedparser sometimes includes score)
    if "reddit" in post.source.lower():
        # Check for high-engagement markers in content
        score_match = re.search(r"(\d+)\s*(?:points?|upvotes?|votes?)", combined)
        if score_match:
            upvotes = int(score_match.group(1))
            if upvotes > 50:
                bonus += 2

    # arXiv: multiple categories signal broader relevance
    if "arxiv" in post.source.lower():
        # arXiv cross-list markers like [cs.NE, q-bio.NC]
        cats = re.findall(r"\b(?:cs|q-bio|stat|math)\.[A-Z]{2}\b", combined, re.IGNORECASE)
        if len(set(cats)) > 1:
            bonus += 2

    # Articles: review / overview / survey get a boost
    for term in ("review", "overview", "survey"):
        if term in title_lower:
            bonus += 1
            break  # Only one bonus per post

    return bonus


# ------------------------------------------------------------------ #
# Deduplication
# ------------------------------------------------------------------ #

def _deduplicate(posts: List[RankedPost]) -> List[RankedPost]:
    """Remove cross-source duplicates, keeping the version from the
    highest-priority source.

    Priority: Quanta > Article > arXiv > NeuroStars > Reddit
    """
    best: Dict[str, RankedPost] = {}
    for post in posts:
        key = post.dedup_key
        if key not in best:
            best[key] = post
        else:
            existing_priority = get_source_priority(best[key].source)
            new_priority = get_source_priority(post.source)
            if new_priority > existing_priority:
                best[key] = post
            elif new_priority == existing_priority and post.final_score > best[key].final_score:
                best[key] = post

    deduped = list(best.values())
    removed = len(posts) - len(deduped)
    if removed:
        log.info("Deduplication removed %d cross-source duplicates", removed)
    return deduped


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #

def rank_posts(
    posts: list[dict],
) -> tuple[list[RankedPost], int, int]:
    """Run the full ranking pipeline.

    Parameters
    ----------
    posts : list[dict]
        Each dict must have keys: ``title``, ``url``, ``source``, ``content``.

    Returns
    -------
    tuple[list[RankedPost], int, int]
        ``(selected_posts, total_analyzed, total_rejected)``
    """
    analyzed = len(posts)
    rejected = 0
    survivors: List[RankedPost] = []

    # ── Stage 1: Filter ──────────────────────────────────────────────
    for p in posts:
        title = p.get("title", "")
        content = p.get("content")
        url = p.get("url", "")
        source = p.get("source", "")

        passes, nrs = passes_relevance(title, content)
        if not passes:
            rejected += 1
            continue

        rp = RankedPost(
            title=title,
            url=url,
            source=source,
            content=content,
            nrs=nrs,
            source_weight=get_source_weight(source),
        )
        survivors.append(rp)

    log.info("Filter: %d passed, %d rejected out of %d", len(survivors), rejected, analyzed)

    # ── Stage 2: Score ───────────────────────────────────────────────
    for rp in survivors:
        rp.popularity_bonus = _popularity_bonus(rp)
        rp.final_score = rp.nrs + rp.source_weight + rp.popularity_bonus
        rp.category = assign_category(rp.source, rp.title, rp.content)

    # ── Stage 3: Deduplicate ─────────────────────────────────────────
    survivors = _deduplicate(survivors)

    # ── Stage 4: Select top N ────────────────────────────────────────
    survivors.sort(key=lambda r: r.final_score, reverse=True)
    selected = survivors[:TOP_N]

    log.info(
        "Ranking complete: top %d selected (scores %d – %d)",
        len(selected),
        selected[0].final_score if selected else 0,
        selected[-1].final_score if selected else 0,
    )

    return selected, analyzed, rejected


def group_by_category(posts: list[RankedPost]) -> dict[str, list[RankedPost]]:
    """Group ranked posts by their assigned category."""
    groups: dict[str, list[RankedPost]] = {}
    for p in posts:
        groups.setdefault(p.category, []).append(p)
    return groups
