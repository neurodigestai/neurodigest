"""Category assignment and source weighting for the ranking engine."""

from __future__ import annotations

# ------------------------------------------------------------------ #
# Source Weights
# ------------------------------------------------------------------ #

_SOURCE_WEIGHTS: dict[str, int] = {
    "arXiv q-bio.NC":          4,
    "arXiv cs.NE":             4,
    "arXiv cs.LG":             3,
    "bioRxiv Neuroscience":    4,
    "Quanta Magazine":         5,
    "Allen Institute":         5,
    "DeepMind Blog":           4,
    "Neuroscience News":       3,
    "The Transmitter":         3,
    "NeuroStars":              3,
    "r/compneuroscience":      2,
    "r/neuroscience":          2,
    "r/MachineLearning":       2,
    "r/NeuroAI":               2,
    "r/cognitivescience":      2,
}

# Default weight for any source not explicitly listed
_DEFAULT_WEIGHT: int = 2


def get_source_weight(source: str) -> int:
    """Return the credibility weight for *source*."""
    return _SOURCE_WEIGHTS.get(source, _DEFAULT_WEIGHT)


# ------------------------------------------------------------------ #
# Source Priority (for deduplication — higher wins)
# ------------------------------------------------------------------ #

_SOURCE_PRIORITY: dict[str, int] = {
    "Quanta Magazine":         50,
    "Neuroscience News":       40,
    "The Transmitter":         40,
    "Allen Institute":         40,
    "DeepMind Blog":           40,
    "arXiv q-bio.NC":          30,
    "arXiv cs.NE":             30,
    "arXiv cs.LG":             30,
    "bioRxiv Neuroscience":    30,
    "NeuroStars":              20,
    "r/compneuroscience":      10,
    "r/neuroscience":          10,
    "r/MachineLearning":       10,
    "r/NeuroAI":               10,
    "r/cognitivescience":      10,
}


def get_source_priority(source: str) -> int:
    """Return the deduplication priority for *source* (higher = keep)."""
    return _SOURCE_PRIORITY.get(source, 5)


# ------------------------------------------------------------------ #
# Category Assignment
# ------------------------------------------------------------------ #

# Category labels
MAJOR_RESEARCH = "Major Research"
UNDERSTANDING  = "Understanding"
COMMUNITY      = "Community"
TOOLS          = "Tools"

# Keywords that signal a "Tools" post
_TOOL_KEYWORDS = [
    "dataset", "software", "toolbox", "toolkit", "library",
    "open source", "benchmark", "framework", "api", "package",
    "pipeline", "platform", "release",
]


def assign_category(source: str, title: str, content: str | None) -> str:
    """Assign a digest category based on source and content signals."""
    text = ((title or "") + " " + (content or "")).lower()

    # Check for tool / dataset / software mentions first
    for kw in _TOOL_KEYWORDS:
        if kw in text:
            return TOOLS

    # Source-based rules
    source_lower = source.lower()
    if any(s in source_lower for s in ("arxiv", "biorxiv")):
        return MAJOR_RESEARCH
    if any(s in source_lower for s in ("reddit", "neurostars")):
        return COMMUNITY
    # News / magazine / blog
    return UNDERSTANDING
