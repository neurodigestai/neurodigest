"""Prompt construction for the LLM summarizer."""

from config_loader import Config

SYSTEM_PROMPT = (
    "You are a helpful research assistant explaining computational neuroscience "
    "and neuro-AI research to a beginner graduate student. Avoid jargon, "
    "mathematics, and equations. Write clearly and simply."
)


def build_summary_prompt(title: str, content: str) -> str:
    """Build the user-facing prompt for summarizing a single post.

    Parameters
    ----------
    title : str
        Article / post title.
    content : str
        Cleaned body text.

    Returns
    -------
    str
        A fully-formed prompt ready to send to the LLM.
    """
    max_words = Config.MAX_SUMMARY_WORDS

    return (
        f"Summarize the following research content.\n"
        f"\n"
        f"Write:\n"
        f"1. One sentence simple explanation\n"
        f"2. Two bullet points describing the finding\n"
        f"3. One bullet point: why it matters\n"
        f"\n"
        f"Maximum {max_words} words.\n"
        f"\n"
        f"Title:\n"
        f"{title}\n"
        f"\n"
        f"Content:\n"
        f"{content}\n"
    )
