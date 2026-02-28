"""Orchestrates LLM summarization with safety checks."""

from __future__ import annotations

import re

from llm_client import generate_completion
from prompt_builder import build_summary_prompt, SYSTEM_PROMPT
from logger import setup_logger

log = setup_logger()

SUMMARY_FAILED_MARKER = "SUMMARY_FAILED"
_MAX_WORD_LIMIT = 150  # hard ceiling for safety check


# ------------------------------------------------------------------ #
# Safety validation
# ------------------------------------------------------------------ #

def _word_count(text: str) -> int:
    return len(text.split())


def _has_equations(text: str) -> bool:
    """Return True if the summary contains LaTeX or math notation."""
    patterns = [
        "$$",
        "\\begin",
        "\\end",
        "\\frac",
        "\\sum",
        "\\int",
        "\\alpha",
        "\\beta",
        "\\theta",
        "\\sigma",
    ]
    for p in patterns:
        if p in text:
            return True
    # Also check for inline LaTeX like $...$
    if re.search(r"\$[^$]+\$", text):
        return True
    return False


def _has_copied_text(summary: str, original: str) -> bool:
    """Return True if the summary contains >30 consecutive characters
    copied verbatim from the original content."""
    if not original:
        return False
    summary_lower = summary.lower()
    original_lower = original.lower()

    # Slide a 30-char window over the summary
    window = 31
    for i in range(len(summary_lower) - window + 1):
        chunk = summary_lower[i : i + window]
        if chunk in original_lower:
            return True
    return False


def _validate_summary(summary: str, original_content: str) -> bool:
    """Return True if the summary passes all safety checks."""
    if _word_count(summary) > _MAX_WORD_LIMIT:
        log.debug("Summary rejected: too long (%d words)", _word_count(summary))
        return False
    if _has_equations(summary):
        log.debug("Summary rejected: contains equations")
        return False
    if _has_copied_text(summary, original_content):
        log.debug("Summary rejected: contains copied text")
        return False
    return True


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #

def summarize_post(title: str, content: str) -> str | None:
    """Generate a validated summary for a single post.

    Calls the LLM, validates the result, and retries once if the first
    attempt fails validation.  Returns ``None`` if both attempts fail
    (caller should mark the post as ``SUMMARY_FAILED``).
    """
    prompt = build_summary_prompt(title, content)

    for attempt in range(2):
        summary = generate_completion(prompt, system_prompt=SYSTEM_PROMPT)

        if summary is None:
            log.warning("LLM returned no output (attempt %d)", attempt + 1)
            continue

        if _validate_summary(summary, content):
            return summary

        log.warning(
            "Summary failed validation (attempt %d) for: %s",
            attempt + 1,
            title[:80],
        )

    return None
