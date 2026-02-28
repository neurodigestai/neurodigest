"""Google Gemini Chat API client (OpenAI-compatible endpoint)."""

from __future__ import annotations

import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config_loader import Config
from logger import setup_logger

log = setup_logger()

# Groq's OpenAI-compatible chat completions endpoint
_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_REQUEST_TIMEOUT = 60  # seconds
_MIN_INTERVAL = 2.0    # seconds between requests (Gemini free tier: 15 RPM)
_last_call_time = 0.0


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=2, min=3, max=15),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    reraise=True,
)
def generate_completion(prompt_text: str, system_prompt: str = "") -> str | None:
    """Send a chat-completion request to the Gemini API.

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

    # Rate-limit: wait if too soon since last call
    elapsed = time.time() - _last_call_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt_text})

    payload = {
        "model": Config.DEEPSEEK_MODEL,  # default: gemini-2.0-flash
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 512,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        resp = requests.post(
            _API_URL,
            json=payload,
            headers=headers,
            timeout=_REQUEST_TIMEOUT,
        )
        _last_call_time = time.time()
        resp.raise_for_status()

        data = resp.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0]["message"]["content"].strip()

        log.warning("Gemini returned empty choices: %s", data)
        return None

    except requests.HTTPError as exc:
        log.error("Gemini API HTTP error: %s — %s", exc, getattr(exc.response, 'text', ''))
        return None
    except Exception as exc:
        log.error("Gemini API unexpected error: %s", exc)
        return None
