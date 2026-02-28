"""NeuroAI Digest -- main entry point.

Run with:
    python main.py
"""

import os
import sys

from config_loader import Config
from logger import setup_logger
from database import (
    initialize_database,
    post_exists,
    insert_post,
    count_posts,
    get_posts_without_content,
    update_post_content,
    get_posts_with_content,
    get_post_summary,
    update_post_summary,
)
from feeds import fetch_all_feeds
from extractor import extract_content
from ranker import rank_posts, group_by_category
from summarizer import summarize_post, SUMMARY_FAILED_MARKER
from summary_refiner import refine_summary
from digest_builder import build_digest
from emailer import send_digest_email, send_digest_to_subscribers
from categories import MAJOR_RESEARCH
from subscribers import get_subscribers
from unsubscribe_handler import filter_unsubscribed


def ensure_directories() -> None:
    """Create any missing project directories (data/, logs/, data/diagrams/)."""
    for directory in ("data", "logs", os.path.join("data", "diagrams")):
        os.makedirs(directory, exist_ok=True)


def main() -> None:
    """Bootstrap the application: load config, init logging, fetch feeds,
    persist new posts, extract content, rank, summarize, refine,
    generate diagrams, and email digest to all subscribers."""

    # 1. Ensure required directories exist
    ensure_directories()

    # 2. Initialise the logger
    log = setup_logger()

    # 3. Startup banner
    print(f"{Config.APP_NAME} starting...")
    print(f"Environment: {Config.APP_ENV}")
    print("Logging initialized")

    log.info("Application starting")
    log.info("Environment: %s", Config.APP_ENV)
    log.info("Logging initialized")

    # 4. Initialise database (includes schema migrations)
    initialize_database()

    # == Phase 1B: Feed ingestion ======================================
    print("Fetching feeds...")
    log.info("Fetching feeds...")
    posts = fetch_all_feeds()
    feeds_count = len(set(p.source for p in posts))

    new_count = 0
    for post in posts:
        if not post_exists(post.url):
            if insert_post(post):
                new_count += 1

    total = count_posts()

    feed_summary = [
        f"Feeds processed: {feeds_count}",
        f"Entries found: {len(posts)}",
        f"New posts stored: {new_count}",
        f"Total stored: {total}",
    ]
    for line in feed_summary:
        print(line)
        log.info(line)

    # == Phase 2: Content extraction ===================================
    pending = get_posts_without_content()
    extracted = 0
    skipped_extract = 0

    if pending:
        print("Extracting content...")
        log.info("Extracting content...")
        log.info("Starting content extraction for %d posts...", len(pending))
        print(f"Extracting content for {len(pending)} posts...")

        for url, source in pending:
            content, is_valid = extract_content(url, source)
            if is_valid and content:
                update_post_content(url, content)
                extracted += 1
            else:
                skipped_extract += 1
                log.debug("Skipped (low content): %s", url)

    extract_lines = [
        f"Extracted content for {extracted} posts",
        f"Skipped {skipped_extract} (low content)",
    ]
    for line in extract_lines:
        print(line)
        log.info(line)

    # == Phase 3: Relevance filtering & ranking ========================
    all_posts = get_posts_with_content()
    selected = []

    if all_posts:
        selected, analyzed, rejected = rank_posts(all_posts)
        grouped = group_by_category(selected)

        rank_lines = [
            "",
            f"Posts analyzed: {analyzed}",
            f"Rejected: {rejected}",
            f"Selected for digest: {len(selected)}",
        ]
        for line in rank_lines:
            print(line)
            if line.strip():
                log.info(line.strip())

        # Show category breakdown
        print("\nDigest preview by category:")
        log.info("Digest preview by category:")
        for category, items in grouped.items():
            print(f"\n  [{category}] ({len(items)} items)")
            log.info("  [%s] (%d items)", category, len(items))
            for item in items:
                print(f"    - [{item.final_score}] {item.title[:80]}")
                log.info("    [score=%d] %s", item.final_score, item.title[:80])
    else:
        print("\nNo posts with content available for ranking.")
        log.warning("No posts with content available for ranking.")

    # == Phase 4: LLM Summarization ====================================
    has_summaries = False

    if selected and Config.DEEPSEEK_API_KEY:
        summaries_generated = 0
        summaries_failed = 0

        print("Generating summaries...")
        log.info("Generating summaries...")
        print(f"Summarizing {len(selected)} selected posts...")
        log.info("Starting LLM summarization for %d posts...", len(selected))

        for rp in selected:
            # Skip if already summarized
            existing = get_post_summary(rp.url)
            if existing and existing != SUMMARY_FAILED_MARKER:
                log.debug("Summary already exists: %s", rp.title[:60])
                summaries_generated += 1
                continue

            summary = summarize_post(rp.title, rp.content or "")
            if summary:
                update_post_summary(rp.url, summary)
                summaries_generated += 1
                log.info("Summarized: %s", rp.title[:60])
            else:
                update_post_summary(rp.url, SUMMARY_FAILED_MARKER)
                summaries_failed += 1
                log.warning("Summary failed: %s", rp.title[:60])

        summary_lines = [
            f"Summaries generated: {summaries_generated}",
            f"Failed: {summaries_failed}",
        ]
        for line in summary_lines:
            print(line)
            log.info(line)

        has_summaries = summaries_generated > 0

    elif selected and not Config.DEEPSEEK_API_KEY:
        print("\n[WARNING] DEEPSEEK_API_KEY not set -- skipping summarization.")
        log.warning("DEEPSEEK_API_KEY not set -- skipping summarization.")

    # == Phase 7A: Summary Refinement ==================================
    if selected and has_summaries and Config.DEEPSEEK_API_KEY:
        print("Refining summaries...")
        log.info("Refining summaries for clarity...")
        refined_count = 0

        for rp in selected:
            original = get_post_summary(rp.url)
            if not original or original == SUMMARY_FAILED_MARKER:
                continue

            refined = refine_summary(original)
            if refined != original:
                update_post_summary(rp.url, refined)
                refined_count += 1

        print(f"Refined {refined_count} summaries")
        log.info("Refined %d summaries", refined_count)

    # == Phase 7B: Diagram Generation ==================================
    if selected and has_summaries and Config.IMAGE_API_KEY:
        # Lazy imports — only needed when image generation is configured
        from diagram_planner import create_diagram_plan
        from diagram_prompt import build_diagram_prompt
        from diagram_generator import generate_diagram
        from image_store import save_diagram, get_diagram_path

        major_research = [
            rp for rp in selected if rp.category == MAJOR_RESEARCH
        ]

        if major_research:
            print(f"Generating diagrams for {len(major_research)} Major Research items...")
            log.info("Generating diagrams for %d Major Research items...",
                     len(major_research))
            diagrams_created = 0
            diagrams_failed = 0

            for rp in major_research:
                # Skip if diagram already exists
                if get_diagram_path(rp.url):
                    log.debug("Diagram already exists: %s", rp.title[:60])
                    diagrams_created += 1
                    continue

                summary = get_post_summary(rp.url)
                if not summary or summary == SUMMARY_FAILED_MARKER:
                    continue

                # Step 1: Plan the diagram
                plan = create_diagram_plan(summary)
                if not plan:
                    log.warning("Diagram plan failed for: %s", rp.title[:60])
                    diagrams_failed += 1
                    continue

                # Step 2: Build the prompt
                prompt = build_diagram_prompt(plan, title=rp.title)

                # Step 3: Generate the image
                image_bytes = generate_diagram(prompt)
                if not image_bytes:
                    log.warning("Image generation failed for: %s", rp.title[:60])
                    diagrams_failed += 1
                    continue

                # Step 4: Save to disk
                path = save_diagram(rp.url, image_bytes)
                if path:
                    diagrams_created += 1
                    log.info("Diagram created: %s", rp.title[:60])
                else:
                    diagrams_failed += 1

            diagram_lines = [
                f"Diagrams created: {diagrams_created}",
                f"Diagrams failed: {diagrams_failed}",
            ]
            for line in diagram_lines:
                print(line)
                log.info(line)

    elif selected and has_summaries and not Config.IMAGE_API_KEY:
        print("[INFO] IMAGE_API_KEY not set -- skipping diagram generation.")
        log.info("IMAGE_API_KEY not set -- skipping diagram generation.")

    # == Phase 5/8: Digest generation & subscriber email ===============
    if selected and has_summaries:
        html, diagram_attachments = build_digest(selected)

        if html:
            item_count = html.count("Read more")
            diagram_count = len(diagram_attachments)
            print(f"\nDigest created with {item_count} items, {diagram_count} diagrams")
            log.info("Digest created with %d items, %d diagrams",
                     item_count, diagram_count)

            # Send email to subscribers
            if Config.EMAIL_APP_PASSWORD:
                print("Sending email...")
                log.info("Sending email...")

                # Phase 8: Get subscriber list and filter unsubscribes
                subscriber_list = get_subscribers()
                subscriber_list = filter_unsubscribed(subscriber_list)

                if subscriber_list:
                    print(f"Sending to {len(subscriber_list)} subscriber(s)...")
                    log.info("Sending digest to %d subscriber(s)...",
                             len(subscriber_list))

                    sent, failed = send_digest_to_subscribers(
                        html,
                        subscriber_list,
                        diagram_attachments=diagram_attachments,
                    )

                    print(f"Emails sent: {sent}, failed: {failed}")
                    log.info("Emails sent: %d, failed: %d", sent, failed)

                    if sent == 0:
                        log.error("All email sends failed")
                else:
                    print("[WARNING] No subscribers found -- skipping email send.")
                    log.warning("No subscribers found -- skipping email send.")
            else:
                print("[WARNING] EMAIL_APP_PASSWORD not set -- skipping email send.")
                log.warning("EMAIL_APP_PASSWORD not set -- skipping email send.")
        else:
            print("\nNo summarized posts available -- digest not generated.")
            log.warning("No summarized posts available -- digest not generated.")

    elif selected and not has_summaries:
        print("\nNo summaries available -- digest and email skipped.")
        log.info("No summaries available -- digest and email skipped.")

    print("\nCompleted successfully.")
    log.info("Completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
