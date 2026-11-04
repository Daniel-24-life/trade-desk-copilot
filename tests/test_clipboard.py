import pytest
from core.clipboard_cleaner import (
    strip_markdown_bold,
    markdown_to_whatsapp,
    markdown_to_plain_text,
    markdown_to_html,
    format_for_target_app
)


def test_strip_markdown_bold():
    raw = "The price is **$9.60 FOB** and MOQ is **100 pcs**."
    cleaned = strip_markdown_bold(raw)
    assert "**" not in cleaned
    assert "$9.60 FOB" in cleaned
    assert "100 pcs" in cleaned


def test_markdown_to_whatsapp():
    raw = "Here is the offer: **$9.60** for **500 units**.\n- Delivery: 18 days"
    wa = markdown_to_whatsapp(raw)
    assert "**" not in wa
    assert "*$9.60*" in wa
    assert "*500 units*" in wa
    assert "• Delivery: 18 days" in wa


def test_host_aware_routing():
    raw = "Thank you! **LT-DL01** has MOQ **20 pcs**."
    res_qianniu = format_for_target_app(raw, app_hint="Qianniu / 阿里国际站")
    assert "**" not in res_qianniu["text"]

    res_wa = format_for_target_app(raw, app_hint="WhatsApp Web")
    assert "*LT-DL01*" in res_wa["text"]
    assert "**" not in res_wa["text"]
