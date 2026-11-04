"""
Trade Desk Copilot - Floating Desktop HUD Workbench
Provides a lightweight floating desktop companion with interactive DST chips,
bilingual translation capsules, quick negotiation chips, and 1080x1080 quotation card preview.
Supports both live global hotkey hook and zero-dependency offline simulation.
"""

import sys
import os
import math
import io
from pathlib import Path
from typing import Dict, Any, List, Optional

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QTextEdit, QLineEdit, QScrollArea, QFrame,
    QGraphicsDropShadowEffect, QButtonGroup, QDialog
)
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QBrush, QPen, QFont,
    QPixmap, QImage, QPainterPath
)

from core.loader import CorpusLoader
from core.agent import (
    TradeDeskAgent,
    STYLE_GOLD_NEGOTIATION,
    STYLE_WHATSAPP_CONCISE,
    STYLE_ENGINEERING_SPEC
)
from core.dst import DialogueState
from core.card_generator import QuotationCardGenerator
from core.mock_engine import MOCK_INQUIRIES
from app.styles import HUD_STYLESHEET


class DSTChip(QPushButton):
    """Interactive chip button that emits slot removal signal upon click."""
    slot_removed = pyqtSignal(str)

    def __init__(self, slot_key: str, label_text: str, parent=None):
        super().__init__(f"{label_text} ✕", parent)
        self.slot_key = slot_key
        self.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #2dd4bf;
                border: 1px solid #0d9488;
                border-radius: 11px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
                border-color: #dc2626;
            }
        """)
        self.clicked.connect(self._on_click)

    def _on_click(self):
        self.slot_removed.emit(self.slot_key)


class CardPreviewDialog(QDialog):
    """High-resolution modal preview for the generated 1080x1080 quotation card."""
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("1080x1080 Visual Quotation Card Preview")
        self.setFixedSize(620, 680)
        self.setStyleSheet("background-color: #0f172a; color: #f8fafc;")

        layout = QVBoxLayout(self)
        img_label = QLabel(self)
        scaled_pixmap = pixmap.scaled(580, 580, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label.setPixmap(scaled_pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)

        btn_box = QHBoxLayout()
        copy_btn = QPushButton("Copy Card Image to Clipboard", self)
        copy_btn.setStyleSheet("""
            background-color: #0d9488; color: white; padding: 8px 16px;
            border-radius: 6px; font-weight: bold;
        """)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setPixmap(pixmap))
        close_btn = QPushButton("Close", self)
        close_btn.setStyleSheet("""
            background-color: #334155; color: white; padding: 8px 16px;
            border-radius: 6px;
        """)
        close_btn.clicked.connect(self.accept)

        btn_box.addWidget(copy_btn)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)


class SpeechBubbleCard(QWidget):
    """Dynamic HUD speech bubble workbench displaying negotiation drafts and controls."""
    def __init__(self, agent: TradeDeskAgent, parent=None):
        super().__init__(parent, Qt.SubWindow | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.agent = agent
        self.current_scenario_idx = 0
        self.current_style = STYLE_GOLD_NEGOTIATION
        self.current_response_data: Dict[str, Any] = {}
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        self.setFixedWidth(520)
        self.setStyleSheet(HUD_STYLESHEET)

        self.main_container = QWidget(self)
        self.main_container.setObjectName("BubbleContainer")
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(16, 14, 16, 14)
        container_layout.setSpacing(10)

        # 1. Header: Buyer & Scenario Info
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Trade Desk Copilot · HUD", self)
        self.title_label.setObjectName("HeaderTitle")
        self.scenario_btn = QPushButton("🔄 Next Scenario", self)
        self.scenario_btn.setStyleSheet("""
            background-color: #1e293b; color: #38bdf8; border: 1px solid #0284c7;
            border-radius: 6px; padding: 4px 8px; font-size: 11px;
        """)
        self.scenario_btn.clicked.connect(self.next_scenario)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.scenario_btn)
        container_layout.addLayout(header_layout)

        # 2. Chinese Translation & Intent Capsule
        self.translation_label = QLabel("Loading scenario...", self)
        self.translation_label.setObjectName("TranslationCapsule")
        self.translation_label.setWordWrap(True)
        container_layout.addWidget(self.translation_label)

        # 3. Interactive DST Slot Chips
        self.chips_container = QWidget(self)
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(6)
        container_layout.addWidget(self.chips_container)

        # 4. Style Switcher
        style_layout = QHBoxLayout()
        self.style_group = QButtonGroup(self)
        self.style_btns: Dict[str, QPushButton] = {}

        styles = [
            (STYLE_GOLD_NEGOTIATION, "🌟 B2B Deal Closing"),
            (STYLE_WHATSAPP_CONCISE, "⚡ WhatsApp Quick"),
            (STYLE_ENGINEERING_SPEC, "📐 Engineering Spec"),
        ]
        for style_key, label in styles:
            btn = QPushButton(label, self)
            btn.setCheckable(True)
            btn.setProperty("class", "StyleButton")
            if style_key == STYLE_GOLD_NEGOTIATION:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, sk=style_key: self.set_style(sk))
            self.style_group.addButton(btn)
            style_layout.addWidget(btn)
            self.style_btns[style_key] = btn
        container_layout.addLayout(style_layout)

        # 5. Dynamic Response Content Area
        self.response_edit = QTextEdit(self)
        self.response_edit.setObjectName("ResponseEdit")
        self.response_edit.setMinimumHeight(140)
        self.response_edit.setMaximumHeight(260)
        container_layout.addWidget(self.response_edit)

        # 6. Quick Action Chips
        quick_layout = QHBoxLayout()
        quick_actions = [
            ("✂️ Shorten 50%", "精简50%"),
            ("📦 Insert CBM", "加上箱规和海运运费参数"),
            ("🏭 Certs/Audit", "提供SGS验厂与CE合规证书"),
            ("🎁 3% Discount", "特批3%折扣支持试单"),
        ]
        for label, cmd in quick_actions:
            q_btn = QPushButton(label, self)
            q_btn.setProperty("class", "ChipButton")
            q_btn.clicked.connect(lambda checked, c=cmd: self.apply_refinement(c))
            quick_layout.addWidget(q_btn)
        container_layout.addLayout(quick_layout)

        # 7. Inline Refinement Input Bar
        self.refine_input = QLineEdit(self)
        self.refine_input.setObjectName("RefineInput")
        self.refine_input.setPlaceholderText("Type instruction (e.g. '改成报$9.20', '加上支持混批')...")
        self.refine_input.returnPressed.connect(self.on_refine_enter)
        container_layout.addWidget(self.refine_input)

        # 8. Bottom Action Bar
        action_layout = QHBoxLayout()
        self.copy_btn = QPushButton("📋 Copy Clean Text", self)
        self.copy_btn.setProperty("class", "PrimaryAction")
        self.copy_btn.clicked.connect(self.copy_clean_text)

        self.card_btn = QPushButton("🖼️ 1080 Quotation Card", self)
        self.card_btn.setProperty("class", "SecondaryAction")
        self.card_btn.clicked.connect(self.open_card_preview)

        action_layout.addWidget(self.copy_btn)
        action_layout.addWidget(self.card_btn)
        container_layout.addLayout(action_layout)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.main_container)

        self.load_scenario(self.current_scenario_idx)

    def load_scenario(self, idx: int):
        scenario = MOCK_INQUIRIES[idx % len(MOCK_INQUIRIES)]
        self.title_label.setText(f"{scenario['buyer_name']} · {scenario['app_hint']}")
        
        session_id = f"sim_session_{scenario['id']}"
        res = self.agent.process_inquiry(
            buyer_message=scenario["message"],
            session_id=session_id,
            buyer_name=scenario["buyer_name"],
            style=self.current_style,
            target_app=scenario["app_hint"]
        )
        self.current_response_data = res

        # Update translation capsule
        self.translation_label.setText(f"【买家原话意图】: {scenario['message']}\n【策略直译】: {res['chinese_summary']}")
        
        # Update response text (using bubble html)
        self.response_edit.setHtml(res["formatted"]["bubble_html"])

        # Refresh DST chips
        self._refresh_chips(res["state"])

    def _refresh_chips(self, state_dict: Dict[str, Any]):
        # Clear existing chips
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add chips for active slots
        if state_dict.get("product_name"):
            short_name = state_dict["product_name"].split("(")[0].strip()
            chip = DSTChip("product", f"Category: {short_name}", self)
            chip.slot_removed.connect(self.remove_slot)
            self.chips_layout.addWidget(chip)

        if state_dict.get("bulk_quantity"):
            chip = DSTChip("bulk_quantity", f"Bulk: {state_dict['bulk_quantity']} pcs", self)
            chip.slot_removed.connect(self.remove_slot)
            self.chips_layout.addWidget(chip)

        if state_dict.get("sample_quantity"):
            chip = DSTChip("sample_quantity", f"Sample: {state_dict['sample_quantity']} pcs", self)
            chip.slot_removed.connect(self.remove_slot)
            self.chips_layout.addWidget(chip)

        if state_dict.get("dimming"):
            chip = DSTChip("dimming", f"Dimming: {state_dict['dimming']}", self)
            chip.slot_removed.connect(self.remove_slot)
            self.chips_layout.addWidget(chip)

        if state_dict.get("destination_zip"):
            chip = DSTChip("destination_zip", f"To: {state_dict['destination_zip']}", self)
            chip.slot_removed.connect(self.remove_slot)
            self.chips_layout.addWidget(chip)

        self.chips_layout.addStretch()

    def remove_slot(self, slot_key: str):
        session_id = self.current_response_data.get("session_id", "default")
        self.agent.dst.remove_slot(session_id, slot_key)
        # Reload current scenario with updated state
        scenario = MOCK_INQUIRIES[self.current_scenario_idx % len(MOCK_INQUIRIES)]
        res = self.agent.process_inquiry(
            buyer_message=scenario["message"],
            session_id=session_id,
            buyer_name=scenario["buyer_name"],
            style=self.current_style,
            target_app=scenario["app_hint"]
        )
        self.current_response_data = res
        self.response_edit.setHtml(res["formatted"]["bubble_html"])
        self._refresh_chips(res["state"])

    def set_style(self, style_key: str):
        self.current_style = style_key
        self.load_scenario(self.current_scenario_idx)

    def next_scenario(self):
        self.current_scenario_idx += 1
        self.load_scenario(self.current_scenario_idx)

    def on_refine_enter(self):
        cmd = self.refine_input.text().strip()
        if cmd:
            self.apply_refinement(cmd)
            self.refine_input.clear()

    def apply_refinement(self, instruction: str):
        current_text = self.current_response_data.get("english_reply", "")
        refined = self.agent.refine_response(current_text, instruction)
        self.current_response_data["english_reply"] = refined
        from core.clipboard_cleaner import format_for_target_app
        formatted = format_for_target_app(refined, app_hint=self.current_response_data.get("intent", {}).get("app_hint", "general"))
        self.current_response_data["formatted"] = formatted
        self.response_edit.setHtml(formatted["bubble_html"])

    def copy_clean_text(self):
        text = self.current_response_data.get("formatted", {}).get("text", "")
        if text:
            QApplication.clipboard().setText(text)
            self.copy_btn.setText("✓ Copied!")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("📋 Copy Clean Text"))

    def open_card_preview(self):
        gen = QuotationCardGenerator()
        state = self.current_response_data.get("state", {})
        data = {
            "brand": "LuminaTech Global Lighting Solutions",
            "category_badge": state.get("product_name", "COMMERCIAL ARCHITECTURAL").upper()[:24],
            "product_title": state.get("product_name", "Architectural LED Fixture"),
            "model_sku": "LT-SERIES-PRO",
            "price_highlight": "From $7.80",
            "specs": [
                {"label": "Rated Power & CCT", "val": "18W COB · 3000K / 4000K"},
                {"label": "Optical Comfort", "val": "Ra > 92 · UGR < 19 Anti-Glare"},
                {"label": "Voltage & Dimming", "val": state.get("dimming", "DALI-2 / 0-10V")},
                {"label": "Logistics & Carton", "val": "24 pcs/ctn · 0.052 CBM"},
            ],
            "commercial": {
                "price_tiers": "$10.50 (MOQ 20) · $9.60 (MOQ 100+)",
                "lead_time": "3-5d Samples · 18-22d Bulk Order",
                "cbm_note": "Export Carton with Corner Protectors",
                "warranty": "5-Year Full Replacement Guarantee",
            },
            "contact": {
                "rep": "Alex Morgan (Sales Director)",
                "email": "sales@luminatech-lighting.com",
                "phone": "+1 (555) 019-2834",
                "url": "https://www.luminatech-lighting.com",
            }
        }
        pil_img = gen.generate(data)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buf.getvalue())
        pixmap = QPixmap.fromImage(qimg)

        dialog = CardPreviewDialog(pixmap, self)
        dialog.exec_()


class FloatingPetWidget(QWidget):
    """Floating desktop companion avatar that docks on the screen edge."""
    def __init__(self, agent: TradeDeskAgent, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.agent = agent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(70, 70)
        self.drag_position = QPoint()

        # Speech bubble
        self.bubble = SpeechBubbleCard(self.agent)
        self.bubble.show()

        # Position at bottom right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 600, screen.height() - 480)
        self.update_bubble_position()

    def update_bubble_position(self):
        self.bubble.move(self.x() + 80, self.y() - 100)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            self.update_bubble_position()
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw glowing teal orb
        center = QPoint(35, 35)
        grad = QRadialGradient(center, 32)
        grad.setColorAt(0.0, QColor(45, 212, 191, 240))  # Teal-400
        grad.setColorAt(0.6, QColor(13, 148, 136, 220))  # Teal-600
        grad.setColorAt(1.0, QColor(15, 23, 42, 0))      # Fade

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, 32, 32)

        # Inner eye / light filament
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPoint(30, 32), 4, 6)
        painter.drawEllipse(QPoint(40, 32), 4, 6)


def run_pet_application():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    agent = TradeDeskAgent()
    pet = FloatingPetWidget(agent)
    pet.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(run_pet_application())
