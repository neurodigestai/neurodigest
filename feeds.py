"""RSS / Atom feed fetcher for the NeuroAI Digest pipeline."""

from __future__ import annotations

from typing import List

import feedparser
import requests

from models import Post
from logger import setup_logger

log = setup_logger()

# ------------------------------------------------------------------ #
# Feed registry — (url, human-readable source name)
# ------------------------------------------------------------------ #
FEED_SOURCES: list[tuple[str, str]] = [
    # Research papers
    ("https://arxiv.org/rss/q-bio.NC",  "arXiv q-bio.NC"),
    ("https://arxiv.org/rss/cs.NE",     "arXiv cs.NE"),
    ("https://arxiv.org/rss/cs.LG",     "arXiv cs.LG"),
    ("https://www.biorxiv.org/collection/neuroscience.xml", "bioRxiv Neuroscience"),

    # Articles
    ("https://neurosciencenews.com/feed/",       "Neuroscience News"),
    ("https://www.thetransmitter.org/feed/",     "The Transmitter"),
    ("https://www.quantamagazine.org/feed/",     "Quanta Magazine"),

    # Discussions
    ("https://neurostars.org/latest.rss",                     "NeuroStars"),
    ("https://www.reddit.com/r/compneuroscience/.rss",        "r/compneuroscience"),
    ("https://www.reddit.com/r/neuroscience/.rss",            "r/neuroscience"),
    ("https://www.reddit.com/r/MachineLearning/.rss",         "r/MachineLearning"),
    ("https://www.reddit.com/r/NeuroAI/.rss",                 "r/NeuroAI"),
    ("https://www.reddit.com/r/cognitivescience/.rss",        "r/cognitivescience"),
]

REQUEST_TIMEOUT = 15  # seconds


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #

def fetch_all_feeds() -> List[Post]:
    """Download every registered feed and return a flat list of
    :class:`Post` objects.

    * Each feed is requested with a 15-second timeout.
    * If a feed fails for *any* reason (network, parse, etc.) the error
      is logged and processing continues with the remaining feeds.
    * Malformed entries inside a successful feed are skipped individually.
    """
    all_posts: List[Post] = []
    feeds_ok = 0

    for url, source_name in FEED_SOURCES:
        try:
            log.info("Fetching feed: %s", source_name)
            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "NeuroAIDigest/1.0"},
            )
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if feed.bozo and not feed.entries:
                log.warning("Feed returned no entries (bozo): %s", source_name)
                continue

            entry_count = 0
            for entry in feed.entries:
                try:
                    post = Post.from_feed_entry(entry, source_name)
                    if post is not None:
                        all_posts.append(post)
                        entry_count += 1
                except Exception as entry_err:
                    log.warning(
                        "Skipping malformed entry in %s: %s",
                        source_name,
                        entry_err,
                    )

            log.info("  → %d entries from %s", entry_count, source_name)
            feeds_ok += 1

        except Exception as feed_err:
            log.warning("Feed failed [%s]: %s", source_name, feed_err)

    log.info("Feeds processed successfully: %d / %d", feeds_ok, len(FEED_SOURCES))
    return all_posts
