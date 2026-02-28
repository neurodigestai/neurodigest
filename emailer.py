"""Gmail SMTP email sender for the Neuro-AI Research Digest."""

from __future__ import annotations

import os
import smtplib
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from config_loader import Config
from logger import setup_logger

log = setup_logger()

_INTER_SEND_DELAY = 5  # seconds between individual subscriber sends


def _build_subject() -> str:
    """Generate the email subject with today's date."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")
    return f"{Config.DIGEST_TITLE} -- {date_str}"


def _build_message(
    html_body: str,
    sender: str,
    recipient: str,
    diagram_attachments: list[dict] | None = None,
) -> MIMEMultipart:
    """Construct the MIME message for a single recipient.

    Parameters
    ----------
    html_body : str
        Complete HTML content.
    sender : str
        From address.
    recipient : str
        To address.
    diagram_attachments : list[dict] | None
        Inline image attachments with ``path`` and ``cid`` keys.

    Returns
    -------
    MIMEMultipart
        Ready-to-send MIME message.
    """
    has_images = bool(diagram_attachments)

    if has_images:
        msg = MIMEMultipart("related")
        msg_alt = MIMEMultipart("alternative")
        msg.attach(msg_alt)
    else:
        msg = MIMEMultipart("alternative")
        msg_alt = msg

    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = _build_subject()

    # Attach HTML body
    msg_alt.attach(MIMEText(html_body, "html", "utf-8"))

    # Attach inline diagram images
    if has_images:
        for att in diagram_attachments:
            path = att.get("path", "")
            cid = att.get("cid", "")
            if not path or not cid or not os.path.isfile(path):
                log.warning("Skipping invalid diagram attachment: %s", path)
                continue
            try:
                with open(path, "rb") as img_file:
                    img_data = img_file.read()
                mime_img = MIMEImage(img_data, _subtype="png")
                mime_img.add_header("Content-ID", f"<{cid}>")
                mime_img.add_header(
                    "Content-Disposition", "inline",
                    filename=os.path.basename(path),
                )
                msg.attach(mime_img)
            except Exception as exc:
                log.warning("Failed to attach diagram %s: %s", path, exc)

    return msg


def _send_single(
    server: smtplib.SMTP,
    sender: str,
    recipient: str,
    msg: MIMEMultipart,
) -> bool:
    """Send a single email via an already-authenticated SMTP connection."""
    try:
        server.sendmail(sender, recipient, msg.as_string())
        log.info("Email sent to %s", recipient)
        return True
    except Exception as exc:
        log.error("Failed to send to %s: %s", recipient, exc)
        return False


def send_digest_email(
    html_body: str,
    recipient: str | None = None,
    diagram_attachments: list[dict] | None = None,
) -> bool:
    """Send the digest HTML email to a single recipient via Gmail SMTP.

    Parameters
    ----------
    html_body : str
        Complete HTML content of the digest.
    recipient : str | None
        Recipient address (defaults to ``Config.EMAIL_ADDRESS``).
    diagram_attachments : list[dict] | None
        Optional inline image attachments.

    Returns
    -------
    bool
        ``True`` if the email was sent successfully.
    """
    sender = Config.EMAIL_ADDRESS
    password = Config.EMAIL_APP_PASSWORD
    to_addr = recipient or sender
    smtp_server = Config.SMTP_SERVER
    smtp_port = Config.SMTP_PORT

    if not sender or not password:
        log.error("EMAIL_ADDRESS or EMAIL_APP_PASSWORD not configured")
        return False

    msg = _build_message(html_body, sender, to_addr, diagram_attachments)

    for attempt in range(2):
        try:
            log.info("Connecting to SMTP server %s:%s (attempt %d)...",
                     smtp_server, smtp_port, attempt + 1)

            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(sender, password)
                server.sendmail(sender, to_addr, msg.as_string())
                log.info("Email sent successfully to %s", to_addr)
                return True

        except smtplib.SMTPAuthenticationError as exc:
            log.error("SMTP authentication failed: %s", exc)
            return False

        except Exception as exc:
            log.error("Email send failed (attempt %d): %s", attempt + 1, exc)
            if attempt == 0:
                log.info("Retrying in 60 seconds...")
                time.sleep(60)

    log.error("Email sending failed after 2 attempts")
    return False


def send_digest_to_subscribers(
    html_body: str,
    subscribers: list[str],
    diagram_attachments: list[dict] | None = None,
) -> tuple[int, int]:
    """Send the digest to a list of subscribers individually.

    Each subscriber receives their own separate email (not CC/BCC).
    A 5-second delay is added between sends to avoid rate limiting.

    Parameters
    ----------
    html_body : str
        Complete HTML content of the digest.
    subscribers : list[str]
        List of email addresses to send to.
    diagram_attachments : list[dict] | None
        Optional inline image attachments.

    Returns
    -------
    tuple[int, int]
        ``(sent_count, failed_count)``
    """
    sender = Config.EMAIL_ADDRESS
    password = Config.EMAIL_APP_PASSWORD
    smtp_server = Config.SMTP_SERVER
    smtp_port = Config.SMTP_PORT

    if not sender or not password:
        log.error("EMAIL_ADDRESS or EMAIL_APP_PASSWORD not configured")
        return 0, len(subscribers)

    if not subscribers:
        log.warning("No subscribers to send to")
        return 0, 0

    sent = 0
    failed = 0

    try:
        log.info("Connecting to SMTP for batch send to %d subscribers...",
                 len(subscribers))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            log.info("SMTP authenticated for batch send")

            for i, subscriber in enumerate(subscribers):
                subscriber = subscriber.strip().lower()
                if not subscriber:
                    continue

                msg = _build_message(
                    html_body, sender, subscriber, diagram_attachments
                )

                success = _send_single(server, sender, subscriber, msg)
                if success:
                    sent += 1
                else:
                    failed += 1

                # Delay between sends (skip for the last one)
                if i < len(subscribers) - 1:
                    time.sleep(_INTER_SEND_DELAY)

    except smtplib.SMTPAuthenticationError as exc:
        log.error("SMTP authentication failed for batch send: %s", exc)
        failed += len(subscribers) - sent

    except Exception as exc:
        log.error("Batch send connection error: %s", exc)
        failed += len(subscribers) - sent

    return sent, failed
