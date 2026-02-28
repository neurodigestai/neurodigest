"""Subscriber management -- reads subscriber emails from Google Sheets."""

from __future__ import annotations

import csv
import io
import re

import requests

from config_loader import Config
from logger import setup_logger

log = setup_logger()

# Regex for basic email validation
_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

_REQUEST_TIMEOUT = 30  # seconds


def _is_valid_email(email: str) -> bool:
    """Return True if the string looks like a valid email address."""
    return bool(_EMAIL_REGEX.match(email.strip()))


def _fetch_sheet_csv(csv_url: str) -> list[str]:
    """Download a Google Sheet as CSV and extract email addresses.

    Parameters
    ----------
    csv_url : str
        The public CSV export URL of the Google Sheet.
        Format: ``https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=csv``

    Returns
    -------
    list[str]
        List of valid email addresses found in the sheet.
    """
    if not csv_url or not csv_url.strip():
        return []

    try:
        resp = requests.get(csv_url.strip(), timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()

        emails: list[str] = []
        reader = csv.reader(io.StringIO(resp.text))

        for row in reader:
            for cell in row:
                cell = cell.strip()
                if _is_valid_email(cell):
                    emails.append(cell.lower())

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for email in emails:
            if email not in seen:
                seen.add(email)
                unique.append(email)

        return unique

    except requests.RequestException as exc:
        log.error("Failed to fetch subscriber sheet: %s", exc)
        return []
    except Exception as exc:
        log.error("Error parsing subscriber CSV: %s", exc)
        return []


def get_subscribers() -> list[str]:
    """Return the list of active subscriber email addresses.

    Reads from the Google Sheet linked to the subscribe form.
    Falls back to the owner's email if no sheet is configured or empty.

    Returns
    -------
    list[str]
        Unique, valid email addresses.
    """
    csv_url = Config.SUBSCRIBERS_SHEET_CSV

    if not csv_url:
        log.info("SUBSCRIBERS_SHEET_CSV not configured — using owner email only")
        owner = Config.EMAIL_ADDRESS
        return [owner] if owner else []

    subscribers = _fetch_sheet_csv(csv_url)

    if subscribers:
        log.info("Loaded %d subscriber(s) from Google Sheet", len(subscribers))
    else:
        log.warning("No subscribers found in sheet — using owner email as fallback")
        owner = Config.EMAIL_ADDRESS
        return [owner] if owner else []

    # Always include the owner email at the top
    owner = Config.EMAIL_ADDRESS.lower() if Config.EMAIL_ADDRESS else ""
    if owner and owner not in subscribers:
        subscribers.insert(0, owner)

    return subscribers
