import re
from pathlib import Path
from core.agent import (
    TradeDeskAgent,
    STYLE_GOLD_NEGOTIATION,
    STYLE_WHATSAPP_CONCISE,
    STYLE_ENGINEERING_SPEC
)
from core.mock_engine import MOCK_INQUIRIES


def test_agent_pipeline_end_to_end():
    agent = TradeDeskAgent()
    sc = MOCK_INQUIRIES[0]  # Dubai luxury hotel

    res = agent.process_inquiry(
        buyer_message=sc["message"],
        session_id="test_pipeline_01",
        buyer_name=sc["buyer_name"],
        style=STYLE_GOLD_NEGOTIATION,
        target_app=sc["app_hint"]
    )

    assert res["intent"]["tier_code"] == "T1"
    assert res["state"]["bulk_quantity"] == 400
    assert "DALI" in res["state"]["dimming"]
    assert len(res["matched_references"]) > 0
    assert "LuminaTech" in res["english_reply"]


def test_agent_styles():
    agent = TradeDeskAgent()
    msg = "Can you send 2 samples of downlight to Germany?"

    res_wa = agent.process_inquiry(msg, style=STYLE_WHATSAPP_CONCISE, target_app="WhatsApp")
    assert "48h" in res_wa["english_reply"] or "samples" in res_wa["english_reply"].lower()

    res_eng = agent.process_inquiry(msg, style=STYLE_ENGINEERING_SPEC, target_app="Outlook")
    assert "Optical & Electrical Specs" in res_eng["english_reply"]


def test_inline_refinement():
    agent = TradeDeskAgent()
    base_text = "Dear Partner,\n\nOur standard price is $10.50 FOB for 100 pcs."
    refined = agent.refine_response(base_text, "改成200台报$9.20")
    assert "$9.20 FOB" in refined
    assert "200 pcs" in refined
    discounted = agent.refine_response(base_text, "特批3%折扣支持试单")
    assert "3% discount" in discounted
    assert "subject to review" in discounted


def test_public_corpus_uses_reserved_email_domains():
    """Public sample contacts use reserved DNS names."""
    corpus = Path(__file__).resolve().parents[1] / "corpus"
    emails = [
        address
        for path in corpus.rglob("*.md")
        for address in re.findall(
            r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b",
            path.read_text(encoding="utf-8"),
            flags=re.I,
        )
    ]
    assert emails
    assert all(address.lower().endswith((".example", ".invalid", "@example.com")) for address in emails)
