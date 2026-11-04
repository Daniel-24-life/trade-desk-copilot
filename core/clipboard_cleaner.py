"""
Host-Aware Clipboard Cleaner & Multi-Platform Formatter
Sanitizes raw AI Markdown outputs for different target chat apps:
- Qianniu / Alibaba International Web / WeChat: Strips bare `**` asterisks and uses clean bullets.
- WhatsApp: Converts `**bold**` to native `*bold*`.
- Outlook / Mail clients: Produces clean plain text and rich HTML.
- UI HUD Bubble: Renders styled HTML with accent highlighted bold parameters.
"""

import re
import html
from typing import Dict, Tuple


def strip_markdown_bold(text: str) -> str:
    """Replaces **bold** with bold."""
    return re.sub(r"\*\*(.*?)\*\*", r"\1", text)


def markdown_to_whatsapp(text: str) -> str:
    """Converts **bold** to WhatsApp native *bold* format."""
    # Convert double asterisks to single
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    # Ensure bullets are clean
    cleaned = re.sub(r"^\s*[\*\-]\s+", "• ", cleaned, flags=re.MULTILINE)
    return cleaned


def markdown_to_plain_text(text: str) -> str:
    """Strips all Markdown markup for IM chats (Qianniu, Alibaba TradeManager, etc.)."""
    cleaned = strip_markdown_bold(text)
    # Remove header markers #, ##, ###
    cleaned = re.sub(r"^\s*#{1,6}\s+", "", cleaned, flags=re.MULTILINE)
    # Convert bullets to clean unicode bullet
    cleaned = re.sub(r"^\s*[\*\-]\s+", "• ", cleaned, flags=re.MULTILINE)
    # Clean code backticks
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    return cleaned.strip()


def markdown_to_html(text: str) -> str:
    """Converts markdown to standard email HTML."""
    escaped = html.escape(text)
    # Bold
    escaped = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped)
    # Paragraphs
    paragraphs = escaped.split("\n\n")
    html_parts = []
    for p in paragraphs:
        lines = p.strip().split("\n")
        # Check if list
        if any(line.strip().startswith("- ") or line.strip().startswith("• ") for line in lines):
            list_items = []
            for line in lines:
                item_text = re.sub(r"^\s*[\-\•]\s*", "", line)
                list_items.append(f"<li>{item_text}</li>")
            html_parts.append(f"<ul>{''.join(list_items)}</ul>")
        else:
            html_parts.append(f"<p>{'<br>'.join(lines)}</p>")
    return "\n".join(html_parts)


def markdown_to_bubble_html(text: str) -> str:
    """
    Renders styled rich HTML for the HUD speech bubble,
    highlighting key commercial metrics in teal/deep slate.
    """
    escaped = html.escape(text)
    # Style bold items as highlighted capsules
    escaped = re.sub(
        r"\*\*(.*?)\*\*",
        r'<b style="color: #0f766e; font-weight: 600; background-color: #ccfbf1; padding: 1px 4px; border-radius: 3px;">\1</b>',
        escaped
    )
    paragraphs = escaped.split("\n\n")
    html_parts = []
    for p in paragraphs:
        p_clean = p.strip().replace("\n", "<br>")
        if p_clean:
            html_parts.append(f'<p style="margin: 4px 0; line-height: 155%;">{p_clean}</p>')
    return "".join(html_parts)


def format_for_target_app(raw_md: str, app_hint: str = "general") -> Dict[str, str]:
    """
    Routes formatting based on target host application window title / process.
    Returns dictionary with 'plain_text', 'whatsapp', and 'html'.
    """
    hint = app_hint.lower()

    if "whatsapp" in hint:
        formatted_text = markdown_to_whatsapp(raw_md)
    elif any(k in hint for k in ["qianniu", "千牛", "alibaba", "trademanager", "chrome", "edge", "wechat"]):
        formatted_text = markdown_to_plain_text(raw_md)
    elif any(k in hint for k in ["outlook", "mail", "foxmail", "thunderbird"]):
        formatted_text = markdown_to_plain_text(raw_md)
    else:
        formatted_text = markdown_to_plain_text(raw_md)

    return {
        "text": formatted_text,
        "whatsapp": markdown_to_whatsapp(raw_md),
        "plain_text": markdown_to_plain_text(raw_md),
        "html": markdown_to_html(raw_md),
        "bubble_html": markdown_to_bubble_html(raw_md),
    }
