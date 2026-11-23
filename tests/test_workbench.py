"""Desktop regressions for actions that must respect reviewed buyer state."""
import os

import pytest

pytest.importorskip("PyQt5.QtWidgets")
from PyQt5.QtWidgets import QApplication

from app.pet import CardPreviewDialog, SpeechBubbleCard
from core.agent import STYLE_WHATSAPP_CONCISE, TradeDeskAgent


@pytest.fixture
def workbench(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    app = QApplication.instance() or QApplication([])
    widget = SpeechBubbleCard(TradeDeskAgent())
    yield widget
    widget.close()
    app.processEvents()


def test_removal_survives_style_switch_and_return_to_scenario(workbench):
    inspection = workbench.current_response_data["state"]
    assert inspection["dimming"] == "DALI-2"
    assert inspection["history_length"] == 1

    workbench.remove_slot("dimming")
    workbench.set_style(STYLE_WHATSAPP_CONCISE)
    workbench.next_scenario()
    assert workbench.current_response_data["state"]["bulk_quantity"] == 300

    workbench.load_scenario(0)
    reviewed = workbench.current_response_data["state"]
    assert reviewed["dimming"] is None
    assert reviewed["bulk_quantity"] == 400
    assert reviewed["turn_count"] == reviewed["history_length"] == 1


def test_quote_preview_handles_missing_product_and_opens_known_product(workbench, monkeypatch):
    calls = []

    def capture_preview(dialog):
        calls.append(dialog.windowTitle())

    monkeypatch.setattr(CardPreviewDialog, "exec_", capture_preview)
    workbench.load_scenario(6)
    assert not workbench.card_btn.isEnabled()
    workbench.open_card_preview()
    assert calls == []

    workbench.load_scenario(1)
    assert workbench.card_btn.isEnabled()
    assert workbench._selected_catalog().metadata["sku"] == "LT-SF30-FOLD"
    workbench.card_btn.click()
    assert len(calls) == 1


def test_copy_uses_the_operator_edited_draft(workbench):
    workbench.response_edit.selectAll()
    workbench.response_edit.insertPlainText("Review the requested voltage first.")
    workbench.copy_clean_text()
    assert QApplication.clipboard().text() == "Review the requested voltage first."
