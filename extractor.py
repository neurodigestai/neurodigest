"""Source-specific content extraction for stored posts."""

from __future__ import annotations

import time
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from cleaner import clean_text
from text_utils import validate_content
from logger import setup_logger

log = setup_logger()

# ------------------------------------------------------------------ #
# HTTP helpers
# ------------------------------------------------------------------ #
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; NeuroAIDigestBot/1.0)",
})
REQUEST_TIMEOUT = 20  # seconds
_LAST_REQUEST_TIME = 0.0
_MIN_REQUEST_INTERVAL = 1.5  # seconds between requests (rate-limiting)


def _fetch_page(url: str) -> str:
    """Download a URL and return the response text.

    Retries up to 3 times on connection / timeout errors with
    exponential back-off.  Enforces a minimum delay between requests
    to avoid hammering servers.
    """
    global _LAST_REQUEST_TIME

    for attempt in range(1, 4):
        elapsed = time.time() - _LAST_REQUEST_TIME
        if elapsed < _MIN_REQUEST_INTERVAL:
            time.sleep(_MIN_REQUEST_INTERVAL - elapsed)

        try:
            resp = _SESSION.get(url, timeout=REQUEST_TIMEOUT)
            _LAST_REQUEST_TIME = time.time()
            resp.raise_for_status()
            return resp.text
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt < 3:
                wait = min(2 ** attempt, 10)
                log.debug("Fetch retry %d for %s (waiting %ds): %s",
                          attempt, url, wait, exc)
                time.sleep(wait)
            else:
                raise


# ------------------------------------------------------------------ #
# Source-specific extractors
# ------------------------------------------------------------------ #

def _extract_arxiv(html: str) -> str:
    """Extract the abstract block from an arXiv abstract page."""
    soup = BeautifulSoup(html, "lxml")

    # Primary: <blockquote class="abstract">
    abstract_tag = soup.find("blockquote", class_="abstract")
    if abstract_tag:
        # Remove the leading "Abstract:" descriptor if present
        desc = abstract_tag.find("span", class_="descriptor")
        if desc:
            desc.decompose()
        return abstract_tag.get_text(separator=" ").strip()

    # Fallback: any element with id="abstract"
    abstract_tag = soup.find(id="abstract")
    if abstract_tag:
        return abstract_tag.get_text(separator=" ").strip()

    return ""


def _extract_biorxiv(html: str) -> str:
    """Extract the abstract from a bioRxiv paper page."""
    soup = BeautifulSoup(html, "lxml")

    # <div class="section abstract">
    abstract_tag = soup.find("div", class_="abstract")
    if abstract_tag:
        return abstract_tag.get_text(separator=" ").strip()

    # Fallback: <section> with id containing "abstract"
    abstract_tag = soup.find("section", id=lambda x: x and "abstract" in x.lower())
    if abstract_tag:
        return abstract_tag.get_text(separator=" ").strip()

    # Fallback: meta tag
    meta = soup.find("meta", attrs={"name": "citation_abstract"})
    if meta and meta.get("content"):
        return meta["content"].strip()

    return ""


def _extract_news_article(html: str) -> str:
    """Extract the main body from a news / magazine article.

    Targets Quanta Magazine, Neuroscience News, The Transmitter, and
    similar sites.  Strips nav/footer/ads and collects <p> tags from
    the main content area.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove noisy elements
    for tag in soup.find_all(["nav", "footer", "header", "aside",
                              "script", "style", "noscript", "iframe"]):
        tag.decompose()

    # Remove common ad / sidebar containers
    import re
    for tag in soup.find_all(
        attrs={"class": re.compile(
            r"(ad-|advert|sidebar|menu|nav|footer|cookie|popup|banner|social|related|newsletter|comment)",
            re.IGNORECASE,
        )}
    ):
        tag.decompose()

    # Try to find the main content container
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=lambda c: c and "content" in c.lower() if c else False)
        or soup.find("div", id=lambda i: i and "content" in i.lower() if i else False)
        or soup.body
    )

    if not main:
        return ""

    paragraphs = main.find_all("p")
    texts = [p.get_text(separator=" ").strip() for p in paragraphs if p.get_text(strip=True)]

    # Require at least 5 paragraphs or 500 words combined
    combined = "\n\n".join(texts)
    word_ct = len(combined.split())
    if len(texts) < 5 and word_ct < 500:
        # Try to get whatever text is available anyway
        combined = main.get_text(separator="\n").strip()

    return combined


def _extract_reddit(html: str) -> str:
    """Extract the post body and top comments from a Reddit page.

    Works with old.reddit / RSS content HTML, and with the new Reddit
    layout when accessed via the ``old.reddit.com`` redirect.
    """
    soup = BeautifulSoup(html, "lxml")

    parts: list[str] = []

    # Post title
    title_tag = soup.find("title")
    if title_tag:
        parts.append(title_tag.get_text(strip=True))

    # Post body — usertext-body or post content
    body = soup.find("div", class_="usertext-body")
    if body:
        parts.append(body.get_text(separator="\n").strip())
    else:
        # Fallback: shreddit-post or post content
        post = soup.find("shreddit-post") or soup.find("div", id="post-content")
        if post:
            parts.append(post.get_text(separator="\n").strip())

    # Top comments (first 5)
    comments = soup.find_all("div", class_="comment")
    if not comments:
        comments = soup.find_all("shreddit-comment")
    for comment in comments[:5]:
        body_div = comment.find("div", class_="usertext-body") or comment
        text = body_div.get_text(separator=" ").strip()
        if text:
            parts.append(f"[Comment] {text}")

    return "\n\n".join(parts)


def _extract_neurostars(html: str) -> str:
    """Extract the question and first 3 answers from a NeuroStars topic."""
    soup = BeautifulSoup(html, "lxml")

    parts: list[str] = []

    # Topic title
    title_tag = soup.find("title")
    if title_tag:
        parts.append(title_tag.get_text(strip=True))

    # In Discourse, posts are in div.post
    posts = soup.find_all("div", class_="post")
    if not posts:
        posts = soup.find_all("article")
    if not posts:
        posts = soup.find_all("div", class_="cooked")

    # First post = question, next 3 = answers
    for i, post in enumerate(posts[:4]):
        cooked = post.find("div", class_="cooked") or post
        text = cooked.get_text(separator="\n").strip()
        if text:
            label = "Question" if i == 0 else f"Answer {i}"
            parts.append(f"[{label}]\n{text}")

    return "\n\n".join(parts)


# ------------------------------------------------------------------ #
# Router
# ------------------------------------------------------------------ #

def _detect_source_type(url: str, source: str) -> str:
    """Return a source-type key based on the URL or feed source name."""
    domain = urlparse(url).netloc.lower()

    if "arxiv.org" in domain:
        return "arxiv"
    if "biorxiv.org" in domain:
        return "biorxiv"
    if "reddit.com" in domain:
        return "reddit"
    if "neurostars.org" in domain:
        return "neurostars"
    # News / magazine sites
    if any(s in domain for s in ("quantamagazine", "neurosciencenews", "thetransmitter")):
        return "news"
    # Fallback by source name
    if "arxiv" in source.lower():
        return "arxiv"
    if "biorxiv" in source.lower():
        return "biorxiv"

    return "news"  # default to generic article extraction


_EXTRACTORS = {
    "arxiv": _extract_arxiv,
    "biorxiv": _extract_biorxiv,
    "news": _extract_news_article,
    "reddit": _extract_reddit,
    "neurostars": _extract_neurostars,
}


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #

def extract_content(url: str, source: str) -> tuple[Optional[str], bool]:
    """Download *url*, extract readable text using a source-specific
    strategy, clean it, and validate length.

    Returns
    -------
    tuple[str | None, bool]
        ``(cleaned_text, is_valid)``

        * ``is_valid=True`` — usable content stored
        * ``is_valid=False`` — low content or extraction failed
    """
    try:
        html = _fetch_page(url)
    except Exception as exc:
        log.warning("Failed to fetch %s: %s", url, exc)
        return None, False

    source_type = _detect_source_type(url, source)
    extractor_fn = _EXTRACTORS.get(source_type, _extract_news_article)

    try:
        raw_text = extractor_fn(html)
    except Exception as exc:
        log.warning("Extraction error for %s (%s): %s", url, source_type, exc)
        return None, False

    if not raw_text or not raw_text.strip():
        return None, False

    cleaned = clean_text(raw_text)
    content, is_valid = validate_content(cleaned)

    return content, is_valid
