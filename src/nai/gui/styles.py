"""Shared styles for all GUI components."""

PACKAGE_CARD_STYLE = """
QFrame#packageCard {
    background-color: #2a2a2a;
    border: 1px solid #6d4aff;
    border-radius: 8px;
    padding: 12px;
}
QFrame#packageCard:hover {
    border-color: #7d5aff;
}
"""

INSTALL_BUTTON_STYLE = """
QPushButton {
    background-color: #6d4aff;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #5a3fd4;
}
"""

UNINSTALL_BUTTON_STYLE = """
QPushButton {
    background-color: #d32f2f;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #b71c1c;
}
"""

SELECTED_BUTTON_STYLE = """
QPushButton {
    background-color: #ffd700;
    color: #000;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #ffcc00;
}
"""

BULK_ACTION_BUTTON_STYLE = """
QPushButton {
    background-color: #3a3a3a;
    color: white;
    border: 1px solid #6d4aff;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #7d5aff;
}
"""

UPDATE_BUTTON_STYLE = """
QPushButton {
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #388e3c;
}
"""
