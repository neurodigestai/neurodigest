"""Unsubscribe handler -- filters out unsubscribed emails."""

from __future__ import annotations

import csv
import io
import re

import requests

from config_loader import Config
from logger import setup_logger

log = setup_logger()

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_REQUEST_TIMEOUT = 30


def _fetch_unsubscribed_emails(csv_url: str) -> set[str]:
    """Download the unsubscribe Google Sheet CSV and return email set.

    Parameters
    ----------
    csv_url : str
        Public CSV export URL of the unsubscribe sheet.

    Returns
    -------
    set[str]
        Set of email addresses that have requested unsubscription.
    """
    if not csv_url or not csv_url.strip():
        return set()

    try:
        resp = requests.get(csv_url.strip(), timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()

        emails: set[str] = set()
        reader = csv.reader(io.StringIO(resp.text))

        for row in reader:
            for cell in row:
                cell = cell.strip()
                if _EMAIL_REGEX.match(cell):
                    emails.add(cell.lower())

        return emails

    except requests.RequestException as exc:
        log.error("Failed to fetch unsubscribe sheet: %s", exc)
        return set()
    except Exception as exc:
        log.error("Error parsing unsubscribe CSV: %s", exc)
        return set()


def filter_unsubscribed(subscribers: list[str]) -> list[str]:
    """Remove unsubscribed emails from the subscriber list.

    Parameters
    ----------
    subscribers : list[str]
        Full list of subscriber emails.

    Returns
    -------
    list[str]
        Filtered list with unsubscribed emails removed.
    """
    csv_url = Config.UNSUBSCRIBE_SHEET_CSV

    if not csv_url:
        log.debug("UNSUBSCRIBE_SHEET_CSV not configured — no filtering applied")
        return subscribers

    unsubscribed = _fetch_unsubscribed_emails(csv_url)

    if not unsubscribed:
        log.debug("No unsubscribe requests found")
        return subscribers

    filtered = [email for email in subscribers if email.lower() not in unsubscribed]
    removed = len(subscribers) - len(filtered)

    if removed:
        log.info("Removed %d unsubscribed email(s) from mailing list", removed)

    return filtered
