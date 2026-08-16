"""Settings/preferences dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFormLayout, QMessageBox,
    QGroupBox, QScrollArea, QWidget,  # <-- Added QWidget
    QFileDialog,
)


class SettingsDialog(QDialog):
    """Application settings dialog."""

    def __init__(self, parent=None, modal=True):
        super().__init__(parent)
        self.setModal(modal)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.form_layout = QFormLayout(self.scroll_content)

        # Library path
        self.library_path_edit = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_library)
        library_layout = QHBoxLayout()
        library_layout.addWidget(self.library_path_edit)
        library_layout.addWidget(browse_btn)
        self.form_layout.addRow("Library Path:", library_layout)

        # Content path
        self.content_path_edit = QLineEdit()
        content_browse_btn = QPushButton("Browse...")
        content_browse_btn.clicked.connect(self._browse_content)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.content_path_edit)
        content_layout.addWidget(content_browse_btn)
        self.form_layout.addRow("Content Path:", content_layout)

        # Install prefix
        self.install_prefix_edit = QLineEdit()
        install_browse_btn = QPushButton("Browse...")
        install_browse_btn.clicked.connect(self._browse_install)
        install_layout = QHBoxLayout()
        install_layout.addWidget(self.install_prefix_edit)
        install_layout.addWidget(install_browse_btn)
        self.form_layout.addRow("Install Prefix:", install_layout)

        # GitHub repo
        self.github_repo_edit = QLineEdit()
        self.form_layout.addRow("GitHub Repo:", self.github_repo_edit)

        # GitHub token
        self.github_token_edit = QLineEdit()
        self.github_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow("GitHub Token:", self.github_token_edit)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        save_btn.setStyleSheet("padding: 10px; font-weight: bold;")

        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)
        layout.addWidget(save_btn)

    def _load_settings(self):
        """Load current settings from config."""
        from nai.config import Config

        config = Config()

        self.library_path_edit.setText(config.get("library_path", ""))
        self.content_path_edit.setText(config.get("content_path", ""))
        self.install_prefix_edit.setText(config.get("install_prefix", ""))
        self.github_repo_edit.setText(config.get("github_repo", ""))
        self.github_token_edit.setText(config.get("github_token", ""))

    def _save_settings(self):
        """Save settings to config."""
        from nai.config import Config

        config = Config()

        config.set("library_path", self.library_path_edit.text())
        config.set("content_path", self.content_path_edit.text())
        config.set("install_prefix", self.install_prefix_edit.text())
        config.set("github_repo", self.github_repo_edit.text())
        config.set("github_token", self.github_token_edit.text())

        config.save()

        QMessageBox.information(self, "Success", "Settings saved successfully!")

    def _browse_library(self):
        """Open directory picker for library path."""
        path = QFileDialog.getExistingDirectory(self, "Select Library Directory")
        if path:
            self.library_path_edit.setText(path)

    def _browse_content(self):
        """Open directory picker for content path."""
        path = QFileDialog.getExistingDirectory(self, "Select Content Directory")
        if path:
            self.content_path_edit.setText(path)

    def _browse_install(self):
        """Open directory picker for install prefix."""
        path = QFileDialog.getExistingDirectory(self, "Select Install Directory")
        if path:
            self.install_prefix_edit.setText(path)
