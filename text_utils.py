"""Text length validation and truncation utilities."""

MIN_WORDS = 200
MAX_WORDS = 4000

LOW_CONTENT_MARKER = "LOW_CONTENT"


def word_count(text: str) -> int:
    """Return the number of whitespace-delimited words in *text*."""
    return len(text.split())


def truncate_to_limit(text: str, max_words: int = MAX_WORDS) -> str:
    """Truncate *text* to at most *max_words* while preserving full
    sentences.

    The function walks backwards from the word-limit boundary to the
    nearest sentence-ending punctuation (``.``, ``!``, ``?``) so the
    output always ends on a complete sentence.
    """
    words = text.split()
    if len(words) <= max_words:
        return text

    truncated = " ".join(words[:max_words])

    # Walk back to the last sentence boundary
    for i in range(len(truncated) - 1, -1, -1):
        if truncated[i] in ".!?":
            return truncated[: i + 1]

    # No sentence boundary found — hard truncate
    return truncated + "..."


def validate_content(text: str) -> tuple[str | None, bool]:
    """Check content length and return processed text.

    Returns
    -------
    tuple[str | None, bool]
        ``(processed_text, is_valid)``

        * If word count < MIN_WORDS → ``(None, False)``  (low content)
        * If word count > MAX_WORDS → ``(truncated_text, True)``
        * Otherwise → ``(text, True)``
    """
    if not text or not text.strip():
        return None, False

    wc = word_count(text)

    if wc < MIN_WORDS:
        return None, False

    if wc > MAX_WORDS:
        return truncate_to_limit(text, MAX_WORDS), True

    return text, True
