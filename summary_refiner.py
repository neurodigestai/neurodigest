"""Summary refiner -- second LLM pass for clarity and readability."""

from __future__ import annotations

from llm_client import generate_completion
from logger import setup_logger

log = setup_logger()

_REFINER_SYSTEM = (
    "You are an expert science communicator. Your job is to rewrite "
    "research summaries so they are crystal-clear to someone with no "
    "technical background. Keep the same meaning, but simplify language."
)

_REFINER_PROMPT_TEMPLATE = (
    "Rewrite the following summary to improve clarity and readability.\n"
    "\n"
    "Rules:\n"
    "• Simplify long or complex sentences\n"
    "• Replace jargon with plain language\n"
    "• Keep the original meaning intact\n"
    "• Maximum 100 words\n"
    "• Keep bullet-point format if present\n"
    "• Do NOT add new information\n"
    "\n"
    "Summary to refine:\n"
    "{summary}\n"
)


def refine_summary(summary: str) -> str:
    """Re-pass a summary through the LLM for clarity improvements.

    Parameters
    ----------
    summary : str
        The original LLM-generated summary.

    Returns
    -------
    str
        A refined, clearer version of the summary.
        Falls back to the original if the LLM call fails.
    """
    if not summary or not summary.strip():
        return summary

    prompt = _REFINER_PROMPT_TEMPLATE.format(summary=summary)

    try:
        refined = generate_completion(prompt, system_prompt=_REFINER_SYSTEM)
        if refined and refined.strip():
            word_count = len(refined.split())
            if word_count <= 120:  # small safety margin above 100
                log.debug("Summary refined (%d → %d words)",
                          len(summary.split()), word_count)
                return refined.strip()
            else:
                log.debug("Refined summary too long (%d words), keeping original", word_count)
                return summary
        else:
            log.debug("Refiner returned empty, keeping original summary")
            return summary
    except Exception as exc:
        log.warning("Summary refinement failed: %s — keeping original", exc)
        return summary
