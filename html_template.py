"""HTML email template for the Neuro-AI Research Digest."""

from __future__ import annotations
from datetime import datetime, timezone

from config_loader import Config


# ------------------------------------------------------------------ #
# Inline styles (no external CSS allowed in HTML emails)
# ------------------------------------------------------------------ #

_BODY_STYLE = (
    "margin: 0; padding: 0; background-color: #f5f5f5; "
    "font-family: Georgia, 'Times New Roman', serif;"
)

_CONTAINER_STYLE = (
    "max-width: 640px; margin: 0 auto; background-color: #ffffff; "
    "padding: 32px 28px; border: 1px solid #e0e0e0;"
)

_HEADER_STYLE = (
    "text-align: center; border-bottom: 2px solid #2c3e50; "
    "padding-bottom: 18px; margin-bottom: 28px;"
)

_TITLE_STYLE = (
    "font-size: 26px; font-weight: bold; color: #2c3e50; "
    "margin: 0 0 6px 0; letter-spacing: 0.5px;"
)

_DATE_STYLE = (
    "font-size: 14px; color: #7f8c8d; margin: 0;"
)

_SECTION_STYLE = (
    "margin-bottom: 28px;"
)

_SECTION_TITLE_STYLE = (
    "font-size: 18px; font-weight: bold; color: #2c3e50; "
    "border-bottom: 1px solid #bdc3c7; padding-bottom: 6px; "
    "margin-bottom: 16px;"
)

_ITEM_STYLE = (
    "margin-bottom: 22px; padding-bottom: 18px; "
    "border-bottom: 1px dotted #ecf0f1;"
)

_ITEM_TITLE_STYLE = (
    "font-size: 16px; font-weight: bold; color: #2980b9; "
    "text-decoration: none;"
)

_SOURCE_STYLE = (
    "font-size: 12px; color: #95a5a6; margin: 4px 0 8px 0;"
)

_SUMMARY_STYLE = (
    "font-size: 14px; color: #34495e; line-height: 1.6; "
    "margin: 0; padding-left: 18px;"
)

_LINK_STYLE = (
    "font-size: 13px; color: #2980b9; text-decoration: none; "
    "font-style: italic;"
)

_FOOTER_STYLE = (
    "text-align: center; font-size: 11px; color: #95a5a6; "
    "border-top: 1px solid #e0e0e0; padding-top: 16px; "
    "margin-top: 28px; line-height: 1.5;"
)


# ------------------------------------------------------------------ #
# Template builder
# ------------------------------------------------------------------ #

def _render_item(title: str, source: str, summary: str, url: str) -> str:
    """Render a single digest item as an HTML block."""
    # Split summary into lines and format as bullet list
    lines = [l.strip() for l in summary.strip().splitlines() if l.strip()]
    bullets_html = ""
    for line in lines:
        # Remove leading bullet markers if present
        clean = line.lstrip("-*").lstrip()
        if clean:
            bullets_html += f'<li style="margin-bottom: 4px;">{clean}</li>\n'

    return f"""
    <div style="{_ITEM_STYLE}">
      <a href="{url}" style="{_ITEM_TITLE_STYLE}" target="_blank">{title}</a>
      <p style="{_SOURCE_STYLE}">Source: {source}</p>
      <ul style="{_SUMMARY_STYLE}">
        {bullets_html}
      </ul>
      <a href="{url}" style="{_LINK_STYLE}" target="_blank">Read more &rarr;</a>
    </div>
    """


def _render_section(section_title: str, items_html: str) -> str:
    """Wrap items in a titled section block."""
    return f"""
    <div style="{_SECTION_STYLE}">
      <h2 style="{_SECTION_TITLE_STYLE}">{section_title}</h2>
      {items_html}
    </div>
    """


def render_digest(
    digest_title: str,
    sections: dict[str, list[dict]],
    unsubscribe_url: str = "",
) -> str:
    """Build the complete HTML email.

    Parameters
    ----------
    digest_title : str
        e.g. "Neuro-AI Research Digest"
    sections : dict[str, list[dict]]
        Mapping of section name to list of item dicts.
        Each item dict must have: ``title``, ``source``, ``summary``, ``url``.

    Returns
    -------
    str
        Complete HTML document ready for email sending.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")

    sections_html = ""
    for section_name, items in sections.items():
        items_html = ""
        for item in items:
            items_html += _render_item(
                title=item["title"],
                source=item["source"],
                summary=item.get("summary", ""),
                url=item["url"],
            )
        if items_html:
            sections_html += _render_section(section_name, items_html)

    # Build unsubscribe link for the footer
    unsub_link = unsubscribe_url or Config.UNSUBSCRIBE_FORM_URL
    if unsub_link:
        unsub_html = (
            f'<p style="margin-top: 10px;">'
            f'<a href="{unsub_link}" style="color: #95a5a6; text-decoration: underline;" '
            f'target="_blank">Unsubscribe</a></p>'
        )
    else:
        unsub_html = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{digest_title}</title>
</head>
<body style="{_BODY_STYLE}">
  <div style="{_CONTAINER_STYLE}">

    <!-- Header -->
    <div style="{_HEADER_STYLE}">
      <h1 style="{_TITLE_STYLE}">{digest_title}</h1>
      <p style="{_DATE_STYLE}">{date_str}</p>
    </div>

    <!-- Sections -->
    {sections_html}

    <!-- Footer -->
    <div style="{_FOOTER_STYLE}">
      <p>You are receiving this because you subscribed to Neuro-AI Research Digest.</p>
      <p>This email contains AI-generated summaries, not original research content.</p>
      {unsub_html}
    </div>

  </div>
</body>
</html>"""
