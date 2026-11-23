"""
Modern Dark Slate & Teal QSS Stylesheet for Trade Desk Copilot HUD
"""

HUD_STYLESHEET = """
QWidget#BubbleContainer {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
}

QLabel#HeaderTitle {
    color: #f8fafc;
    font-size: 14px;
    font-weight: bold;
    font-family: "Segoe UI", "Inter", "Microsoft YaHei UI", sans-serif;
}

QLabel#TranslationCapsule {
    color: #94a3b8;
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
}

QTextEdit#ResponseEdit {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
    font-family: "Segoe UI", "Inter", "Microsoft YaHei UI", sans-serif;
    selection-background-color: #0d9488;
}

QLineEdit#RefineInput {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
}
QLineEdit#RefineInput:focus {
    border: 1px solid #0d9488;
}

QPushButton.StyleButton {
    background-color: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton.StyleButton:hover {
    background-color: #334155;
    color: #f8fafc;
}
QPushButton.StyleButton:checked {
    background-color: #0f766e;
    color: #ffffff;
    border: 1px solid #14b8a6;
}

QPushButton.ChipButton {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
}
QPushButton.ChipButton:hover {
    background-color: #334155;
    border-color: #0d9488;
    color: #2dd4bf;
}

QPushButton.PrimaryAction {
    background-color: #0f766e;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: bold;
}
QPushButton.PrimaryAction:hover {
    background-color: #115e59;
}

QPushButton.SecondaryAction {
    background-color: #334155;
    color: #f8fafc;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton.SecondaryAction:hover {
    background-color: #475569;
}

QPushButton.SecondaryAction:disabled {
    background-color: #1e293b;
    color: #94a3b8;
}

QPushButton:focus {
    border: 1px solid #5eead4;
}
"""
