import os
import pytest
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


def test_sanitization_zero_leakage():
    """Verifies that none of the confidential enterprise markers exist in the new codebase or corpus."""
    project_root = Path(__file__).resolve().parent.parent
    # Split forbidden tokens into fragments so this test file itself doesn't trigger false positives
    forbidden_tokens = [
        "".join(["安", "鼎", "晟"]),
        "".join(["品", "诺"]),
        "".join(["陈", "文", "燕"]),
        "".join(["137", "1408", "7245"]),
        "".join(["916461264", "@", "qq.com"]),
        "".join(["andinsun", ".", "en", ".alibaba.com"])
    ]

    this_file = Path(__file__).resolve()
    scanned_files = 0
    for root, _, files in os.walk(project_root):
        if ".git" in root or "__pycache__" in root or ".pytest_cache" in root:
            continue
        for f in files:
            if f.endswith((".py", ".md", ".txt", ".json", ".yml")):
                file_path = Path(root) / f
                if file_path == this_file:
                    continue
                scanned_files += 1
                content = file_path.read_text(encoding="utf-8")
                for tok in forbidden_tokens:
                    assert tok not in content, f"Sensitive token '{tok}' leaked in {file_path}!"

    assert scanned_files >= 10, f"Expected to scan at least 10 files, scanned {scanned_files}"
