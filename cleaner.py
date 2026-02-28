"""Text cleaning utilities for extracted web content."""

import re
from bs4 import BeautifulSoup


def strip_html(raw_html: str) -> str:
    """Remove all HTML tags, scripts, styles, and return plain text."""
    soup = BeautifulSoup(raw_html, "lxml")

    # Remove script and style elements entirely
    for tag in soup.find_all(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    # Remove navigation, footer, ads, sidebars
    for tag in soup.find_all(
        ["nav", "footer", "header", "aside"],
    ):
        tag.decompose()

    # Remove elements by common ad/nav class/id patterns
    for tag in soup.find_all(
        attrs={"class": re.compile(
            r"(ad-|advert|sidebar|menu|nav|footer|cookie|popup|banner|social)",
            re.IGNORECASE,
        )}
    ):
        tag.decompose()

    text = soup.get_text(separator="\n")
    return text


def remove_citations(text: str) -> str:
    """Remove inline citation markers like [1], [2,3], [1-5]."""
    # Matches [1], [12], [1,2,3], [1-5], [1, 2], etc.
    return re.sub(r"\[\d+(?:[,\-–]\s*\d+)*\]", "", text)


def remove_references_section(text: str) -> str:
    """Remove the references / bibliography block that often appears at
    the end of academic pages."""
    # Look for a line that says "References" (or similar) and cut everything after
    patterns = [
        r"(?m)^#{0,3}\s*References\s*$",
        r"(?m)^#{0,3}\s*Bibliography\s*$",
        r"(?m)^#{0,3}\s*Works\s+Cited\s*$",
        r"(?m)^#{0,3}\s*REFERENCES\s*$",
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            text = text[: match.start()]
            break
    return text


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces / newlines."""
    # Replace multiple blank lines with a single one
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse horizontal whitespace (but keep newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines)


def clean_text(raw_html_or_text: str) -> str:
    """Full cleaning pipeline: HTML → plain text → citation removal →
    reference removal → whitespace collapse."""
    text = strip_html(raw_html_or_text)
    text = remove_citations(text)
    text = remove_references_section(text)
    text = collapse_whitespace(text)
    return text.strip()
