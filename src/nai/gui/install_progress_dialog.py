"""Installation progress dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame,
)


class InstallProgressDialog(QDialog):
    """Dialog showing installation progress."""

    def __init__(self, package_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Installing {package_id}...")
        self.setFixedSize(500, 200)
        self.setModal(True)
        self._setup_ui(package_id)

    def _setup_ui(self, package_id: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel(f"Installing: {package_id}")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a1a;
                border: 1px solid #3d0c5c;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #6d4aff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Preparing...")
        self.status_label.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        layout.addWidget(self.status_label)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #3d0c5c; max-height: 1px;")
        layout.addWidget(divider)

        # Close button (hidden until complete)
        self.close_btn = QPushButton("Close")
        self.close_btn.setVisible(False)
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)

    def update_progress(self, percent: int, status: str):
        """Update progress bar and status text."""
        self.progress_bar.setValue(percent)
        self.status_label.setText(status)

    def set_complete(self):
        """Mark installation as complete."""
        self.progress_bar.setValue(100)
        self.status_label.setStyleSheet("color: #00cc66;")
        self.status_label.setText("Installation complete!")
        self.cancel_btn.setVisible(False)
        self.close_btn.setVisible(True)

    def set_error(self, error_message: str):
        """Mark installation as failed."""
        self.status_label.setStyleSheet("color: #ff4444;")
        self.status_label.setText(f"Error: {error_message}")
        self.cancel_btn.setVisible(False)
        self.close_btn.setVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #ff4444;
            }
        """)
