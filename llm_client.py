"""Groq Chat API client (OpenAI-compatible endpoint)."""

from __future__ import annotations

import re
import time
import requests

from config_loader import Config
from logger import setup_logger

log = setup_logger()

# Groq's OpenAI-compatible chat completions endpoint
_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_REQUEST_TIMEOUT = 60  # seconds
_MIN_INTERVAL = 4.0    # seconds between requests (Groq free tier: 12k TPM)
_MAX_RETRIES = 3       # total attempts on rate-limit / transient errors
_last_call_time = 0.0


def _parse_retry_after(response_text: str) -> float:
    """Try to extract the suggested wait time from a Groq 429 response."""
    match = re.search(r"Please try again in ([\d.]+)s", response_text)
    if match:
        return float(match.group(1)) + 1.0  # add 1s margin
    return 10.0  # safe default


def generate_completion(prompt_text: str, system_prompt: str = "") -> str | None:
    """Send a chat-completion request to the Groq API.

    Handles 429 rate-limit errors by parsing the suggested wait time
    from the response body and retrying up to ``_MAX_RETRIES`` times.

    Parameters
    ----------
    prompt_text : str
        The user message (the actual prompt).
    system_prompt : str
        Optional system-level instruction.

    Returns
    -------
    str | None
        The assistant's reply text, or ``None`` on failure.
    """
    global _last_call_time

    api_key = Config.DEEPSEEK_API_KEY  # env var name kept for backward compat
    if not api_key:
        log.error("LLM API key is not set — cannot generate completion")
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt_text})

    payload = {
        "model": Config.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 512,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    for attempt in range(1, _MAX_RETRIES + 1):
        # Rate-limit: wait if too soon since last call
        elapsed = time.time() - _last_call_time
        if elapsed < _MIN_INTERVAL:
            time.sleep(_MIN_INTERVAL - elapsed)

        try:
            resp = requests.post(
                _API_URL,
                json=payload,
                headers=headers,
                timeout=_REQUEST_TIMEOUT,
            )
            _last_call_time = time.time()

            # Handle rate-limit (429) with retry
            if resp.status_code == 429:
                body = resp.text
                wait_time = _parse_retry_after(body)
                log.warning(
                    "Rate limited (attempt %d/%d), waiting %.1fs...",
                    attempt, _MAX_RETRIES, wait_time,
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(wait_time)
                    continue
                else:
                    log.error("Rate limited after %d attempts, giving up", _MAX_RETRIES)
                    return None

            resp.raise_for_status()

            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0]["message"]["content"].strip()

            log.warning("API returned empty choices: %s", data)
            return None

        except requests.HTTPError as exc:
            log.error("API HTTP error (attempt %d): %s — %s",
                      attempt, exc, getattr(exc.response, 'text', ''))
            if attempt < _MAX_RETRIES:
                time.sleep(5)
                continue
            return None

        except (requests.ConnectionError, requests.Timeout) as exc:
            log.warning("Connection error (attempt %d/%d): %s", attempt, _MAX_RETRIES, exc)
            if attempt < _MAX_RETRIES:
                time.sleep(5)
                continue
            return None

        except Exception as exc:
            log.error("Unexpected API error: %s", exc)
            return None

    return None
