"""Diagram generator -- calls an image generation API to produce PNGs."""

from __future__ import annotations

import base64
import os
import requests

from config_loader import Config
from logger import setup_logger

log = setup_logger()

# Supported providers and their API endpoints
_PROVIDERS = {
    "deepseek": "https://api.deepseek.com/images/generations",
    "openai": "https://api.openai.com/v1/images/generations",
    "stability": "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
}

_REQUEST_TIMEOUT = 120  # seconds — image gen can be slow


def _generate_openai_compatible(prompt: str, api_key: str, api_url: str) -> bytes | None:
    """Call an OpenAI-compatible image generation endpoint.

    Works with OpenAI, DeepSeek, and other compatible APIs.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json",
    }

    try:
        resp = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        data = resp.json()
        images = data.get("data", [])
        if images and "b64_json" in images[0]:
            return base64.b64decode(images[0]["b64_json"])

        # Some APIs return a URL instead of base64
        if images and "url" in images[0]:
            img_resp = requests.get(images[0]["url"], timeout=60)
            img_resp.raise_for_status()
            return img_resp.content

        log.warning("Image API returned no image data")
        return None

    except requests.HTTPError as exc:
        log.error("Image API HTTP error: %s", exc)
        return None
    except Exception as exc:
        log.error("Image API unexpected error: %s", exc)
        return None


def _generate_stability(prompt: str, api_key: str) -> bytes | None:
    """Call the Stability AI REST API."""
    url = _PROVIDERS["stability"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    payload = {
        "text_prompts": [{"text": prompt, "weight": 1}],
        "cfg_scale": 7,
        "width": 1024,
        "height": 1024,
        "samples": 1,
        "steps": 30,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()

        data = resp.json()
        artifacts = data.get("artifacts", [])
        if artifacts and "base64" in artifacts[0]:
            return base64.b64decode(artifacts[0]["base64"])

        log.warning("Stability API returned no artifacts")
        return None

    except requests.HTTPError as exc:
        log.error("Stability API HTTP error: %s", exc)
        return None
    except Exception as exc:
        log.error("Stability API unexpected error: %s", exc)
        return None


def generate_diagram(prompt: str) -> bytes | None:
    """Generate a diagram image from a text prompt.

    Uses the provider configured in ``Config.IMAGE_MODEL_PROVIDER``
    and the API key from ``Config.IMAGE_API_KEY``.

    Parameters
    ----------
    prompt : str
        The image generation prompt.

    Returns
    -------
    bytes | None
        Raw PNG/image bytes, or ``None`` on failure.
    """
    provider = Config.IMAGE_MODEL_PROVIDER.lower().strip()
    api_key = Config.IMAGE_API_KEY

    if not provider or not api_key:
        log.warning("IMAGE_MODEL_PROVIDER or IMAGE_API_KEY not configured — skipping diagram")
        return None

    log.info("Generating diagram via %s...", provider)

    if provider in ("openai", "deepseek"):
        api_url = _PROVIDERS.get(provider)
        return _generate_openai_compatible(prompt, api_key, api_url)
    elif provider == "stability":
        return _generate_stability(prompt, api_key)
    else:
        # Treat unknown providers as OpenAI-compatible using a custom URL
        log.info("Unknown provider '%s' — attempting OpenAI-compatible API", provider)
        custom_url = os.getenv("IMAGE_API_URL", _PROVIDERS["openai"])
        return _generate_openai_compatible(prompt, api_key, custom_url)
