"""GUI launcher for Nobara Audio Installer."""

import os
import sys
from pathlib import Path

# Workaround for Wayland display issues
os.environ["QT_QPA_PLATFORM"] = os.environ.get("QT_QPA_PLATFORM", "wayland;xcb")

# Add src directory to path
SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

def launch():
    """Launch the NAI GUI application."""
    from PyQt5.QtWidgets import QApplication
    from nai.gui.main_window import MainWindow

    # Create application with fixed styling
    app = QApplication(sys.argv)
    app.setApplicationName("Nobara Audio Installer")
    app.setStyle("Fusion")

    # Apply Lumo purple/dark theme (fixed, no user choice)
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1a1a1a;
        }

        QWidget {
            color: #ffffff;
            background-color: #1a1a1a;
        }

        QTabWidget::pane {
            border: 1px solid #6d4aff;
            background-color: #1a1a1a;
            border-radius: 4px;
        }

        QTabBar::tab {
            background-color: #2a2a2a;
            color: #cccccc;
            padding: 8px 16px;
            border: 1px solid #6d4aff;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 100px;
        }

        QTabBar::tab:selected {
            background-color: #6d4aff;
            color: #ffffff;
        }

        QTabBar::tab:hover:!selected {
            background-color: #3a3a3a;
        }

        QPushButton {
            background-color: #6d4aff;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #5a3fd4;
        }

        QPushButton:pressed {
            background-color: #4a33b8;
        }

        QLineEdit {
            background-color: #2a2a2a;
            border: 1px solid #6d4aff;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
        }

        QLineEdit:focus {
            border: 2px solid #6d4aff;
        }

        QComboBox {
            background-color: #2a2a2a;
            border: 1px solid #6d4aff;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
        }

        QComboBox::drop-down {
            border: none;
        }

        QCheckBox {
            color: #ffffff;
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #6d4aff;
            border-radius: 3px;
            background-color: #2a2a2a;
        }

        QCheckBox::indicator:checked {
            background-color: #6d4aff;
            border: 2px solid #6d4aff;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }

        QFrame {
            background-color: #2a2a2a;
        }

        QLabel {
            color: #ffffff;
        }

        QStatusBar {
            background-color: #2a2a2a;
            color: #cccccc;
            border-top: 1px solid #6d4aff;
        }

        QMenu {
            background-color: #2a2a2a;
            border: 1px solid #6d4aff;
            color: #ffffff;
        }

        QMenu::item:selected {
            background-color: #6d4aff;
        }

        QMessageBox {
            background-color: #2a2a2a;
        }

        QTextEdit {
            background-color: #2a2a2a;
            border: 1px solid #6d4aff;
            border-radius: 4px;
            padding: 8px;
            color: #ffffff;
        }
    """)

    # Force show window on front
    window = MainWindow()
    window.show()
    window.activateWindow()
    window.raise_()

    # Run the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    launch()
