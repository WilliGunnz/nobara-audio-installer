"""Main window for NAI GUI."""

import json
import subprocess
import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QStatusBar,
    QMenuBar,
    QMenu,
    QAction,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QTextEdit,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QFrame,
    QProgressBar,
    QApplication,
)
from PyQt5.QtCore import Qt

from nai.gui.package_browser import PackageBrowserWidget
from nai.config import Config, get_my_plugins, set_my_plugins
from nai.installer.uninstall import list_installed

# Import shared styles
from .styles import (
    PACKAGE_CARD_STYLE,
    INSTALL_BUTTON_STYLE,
    UNINSTALL_BUTTON_STYLE,
    SELECTED_BUTTON_STYLE,
    BULK_ACTION_BUTTON_STYLE,
    UPDATE_BUTTON_STYLE,
)

class PackagesTabWidget(QWidget):
    """Tab showing available NAI packages from manifest with install."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = Config()
        self._packages = []
        self._installed_ids = set()
        self._selected_ids = set()

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()

        title = QLabel("Available Packages")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setStyleSheet(BULK_ACTION_BUTTON_STYLE)
        self.select_all_btn.clicked.connect(self._select_all)
        header.addWidget(self.select_all_btn)

        self.unselect_all_btn = QPushButton("Unselect All")
        self.unselect_all_btn.setStyleSheet(BULK_ACTION_BUTTON_STYLE)
        self.unselect_all_btn.clicked.connect(self._unselect_all)
        header.addWidget(self.unselect_all_btn)

        self.install_all_btn = QPushButton("Install Selected")
        self.install_all_btn.setStyleSheet(BULK_ACTION_BUTTON_STYLE)
        self.install_all_btn.clicked.connect(self._install_selected)
        header.addWidget(self.install_all_btn)

        self.uninstall_all_btn = QPushButton("Uninstall Selected")
        self.uninstall_all_btn.setStyleSheet(BULK_ACTION_BUTTON_STYLE)
        self.uninstall_all_btn.clicked.connect(self._uninstall_selected)
        header.addWidget(self.uninstall_all_btn)

        self.check_updates_btn = QPushButton("✓ Check for Updates")
        self.check_updates_btn.setStyleSheet(UPDATE_BUTTON_STYLE)
        self.check_updates_btn.clicked.connect(self._check_updates)
        header.addWidget(self.check_updates_btn)

        layout.addLayout(header)

        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["all", "lv2", "vst3", "vst", "clap",
                                       "drum-packs", "ir-packs", "midi-packs",
                                       "presets", "soundfonts"])
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self.category_combo)

        filter_layout.addSpacing(16)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        self.search_input.setMinimumWidth(250)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #6d4aff;
                border-radius: 4px;
                font-size: 14px;
                background-color: #2a2a2a;
                color: white;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        filter_layout.addWidget(self.search_input)

        filter_layout.addStretch()

        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setToolTip("Refresh package list")
        refresh_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(8)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(4)

        self.progress_status = QLabel("")
        self.progress_status.setStyleSheet("color: #888; font-size: 12px; min-height: 20px;")
        self.progress_status.setMinimumHeight(20)
        progress_layout.addWidget(self.progress_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #6d4aff;
                border-radius: 4px;
                background-color: #2a2a2a;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #6d4aff;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        layout.addLayout(progress_layout)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.info_label)

    def _set_progress(self, visible: bool, message: str = "", value: int = 0, maximum: int = 100):
        """Update progress indicator."""
        if self.progress_bar is None:
            return
        self.progress_bar.setVisible(visible)
        if visible:
            self.progress_bar.setMaximum(maximum)
            self.progress_bar.setValue(value)
            self.progress_status.setText(message)
        else:
            self.progress_status.setText("")
        QApplication.processEvents()

    def refresh(self):
        """Refresh available packages from manifest and installed status."""
        if self.content_layout is None:
            return

        content_path = self._config.get("content_path", "")
        if content_path:
            manifest_path = Path(content_path) / "packages.json"
            packages = self._load_manifest(manifest_path)
        else:
            packages = []

        self._installed_ids = {pkg.get("id") for pkg in list_installed()}

        self._packages = []
        for pkg in packages:
            pkg_data = {
                "id": pkg.get("id", ""),
                "name": pkg.get("name", pkg.get("id", "")),
                "version": pkg.get("version", "1.0.0"),
                "category": pkg.get("category", "unknown"),
                "description": pkg.get("description", ""),
                "download": pkg.get("download", ""),
                "sha256": pkg.get("sha256", ""),
                "size": pkg.get("size", 0),
                "is_installed": pkg.get("id") in self._installed_ids,
                "is_selected": pkg.get("id") in self._selected_ids,
            }
            self._packages.append(pkg_data)

        self._render_cards()

    def _load_manifest(self, manifest_path: Path) -> list:
        """Load packages from manifest JSON."""
        if not manifest_path.exists():
            return []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("packages", [])
        except (json.JSONDecodeError, IOError):
            return []

    def _on_category_changed(self, category: str):
        """Handle category filter change."""
        self._render_cards()

    def _on_search(self):
        """Handle search input."""
        query = self.search_input.text().lower()
        self._apply_filter(query)

    def _apply_filter(self, query: str = ""):
        """Apply search filter and re-render."""
        self._render_cards()

    def _render_cards(self):
        """Render package cards."""
        if self.content_layout is None:
            return

        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        category = self.category_combo.currentText() if hasattr(self, 'category_combo') else "all"
        query = self.search_input.text().lower() if self.search_input else ""

        filtered = self._packages

        if category != "all":
            filtered = [p for p in filtered if p.get("category") == category]

        if query:
            filtered = [
                p for p in filtered
                if query in p.get("id", "").lower()
                or query in p.get("name", "").lower()
                or query in p.get("category", "").lower()
            ]

        if not filtered:
            msg = "No packages found"
            if query or category != "all":
                msg += " matching your criteria"

            label = QLabel(msg)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("padding: 32px; color: #888;")
            self.content_layout.addWidget(label)
        else:
            for pkg in filtered:
                card = self._create_package_card(pkg)
                self.content_layout.addWidget(card)

        total = len(self._packages)
        shown = len(filtered)
        installed = sum(1 for p in filtered if p.get("is_installed"))
        selected = sum(1 for p in filtered if p.get("id") in self._selected_ids)
        self.info_label.setText(
            f"Showing {shown} of {total} packages ({installed} installed, {selected} selected)"
        )

    def _create_package_card(self, pkg: dict) -> QFrame:
        """Create a single package card widget."""
        card = QFrame()
        card.setObjectName("packageCard")
        card.setStyleSheet(PACKAGE_CARD_STYLE)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        top_row = QHBoxLayout()

        is_selected = pkg["id"] in self._selected_ids
        select_checkbox = QPushButton("☑" if is_selected else "☐")
        select_checkbox.setFixedSize(32, 32)
        select_checkbox.setStyleSheet(SELECTED_BUTTON_STYLE if is_selected else BULK_ACTION_BUTTON_STYLE)
        select_checkbox.setToolTip("Include in bulk operations")
        select_checkbox.clicked.connect(lambda checked: self._toggle_selection(pkg["id"]))
        top_row.addWidget(select_checkbox)

        name_label = QLabel(f"<b>{pkg.get('name', 'Unknown')}</b>")
        name_label.setStyleSheet("font-size: 16px;")
        top_row.addWidget(name_label)

        top_row.addStretch()

        if pkg.get("is_installed"):
            status_label = QLabel("✓ Installed")
            status_label.setStyleSheet("color: #4caf50; font-size: 13px;")
            top_row.addWidget(status_label)

            uninstall_btn = QPushButton("Uninstall")
            uninstall_btn.setFixedWidth(90)
            uninstall_btn.setStyleSheet(UNINSTALL_BUTTON_STYLE)
            uninstall_btn.clicked.connect(lambda checked: self._uninstall_package(pkg["id"]))
            top_row.addWidget(uninstall_btn)
        else:
            install_btn = QPushButton("Install")
            install_btn.setFixedWidth(90)
            install_btn.setStyleSheet(INSTALL_BUTTON_STYLE)
            install_btn.clicked.connect(lambda checked: self._install_package(pkg["id"]))
            top_row.addWidget(install_btn)

        layout.addLayout(top_row)

        meta_layout = QHBoxLayout()
        ver_label = QLabel(f"v{pkg.get('version', '1.0.0')} • {pkg.get('category', 'unknown')}")
        ver_label.setStyleSheet("color: #aaa; font-size: 13px;")
        meta_layout.addWidget(ver_label)

        size = pkg.get("size", 0)
        if size:
            size_str = self._format_size(size)
            size_label = QLabel(f"{size_str}")
            size_label.setStyleSheet("color: #888; font-size: 12px;")
            meta_layout.addWidget(size_label)

        meta_layout.addStretch()
        layout.addLayout(meta_layout)

        description = pkg.get("description", "")
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #ccc; font-size: 13px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        return card

    def _format_size(self, size_bytes: int) -> str:
        """Format byte count to human-readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _toggle_selection(self, package_id: str):
        """Toggle selection status for a package."""
        if package_id in self._selected_ids:
            self._selected_ids.remove(package_id)
        else:
            self._selected_ids.add(package_id)
        self._render_cards()

    def _select_all(self):
        """Select all displayed packages."""
        category = self.category_combo.currentText() if hasattr(self, 'category_combo') else "all"
        query = self.search_input.text().lower() if self.search_input else ""

        packages_to_select = self._packages.copy()
        if category != "all":
            packages_to_select = [p for p in packages_to_select if p.get("category") == category]
        if query:
            packages_to_select = [
                p for p in packages_to_select
                if query in p.get("id", "").lower()
                or query in p.get("name", "").lower()
            ]

        self._selected_ids.update(p.get("id") for p in packages_to_select)
        self._render_cards()

    def _unselect_all(self):
        """Unselect all packages."""
        self._selected_ids.clear()
        self._render_cards()

    def _install_package(self, package_id: str):
        """Install a package using nai install CLI."""
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Installation",
                f"Install {package_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self._set_progress(True, f"Downloading and installing {package_id}...", 0, 0)

                process = subprocess.Popen(
                    ["nai", "install", package_id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=120)

                self._set_progress(False)

                if process.returncode == 0:
                    QMessageBox.information(self, "Success", f"Installed {package_id}")
                    self.refresh()
                else:
                    QMessageBox.critical(
                        self,
                        "Installation Failed",
                        f"Failed to install {package_id}:\n{stderr}"
                    )

        except subprocess.TimeoutExpired:
            self._set_progress(False)
            QMessageBox.critical(self, "Timeout", "Installation timed out")
        except Exception as e:
            self._set_progress(False)
            QMessageBox.critical(self, "Error", f"Installation failed:\n{str(e)}")

    def _install_selected(self):
        """Install all selected packages - ONE command, installs all at once."""
        selected_not_installed = [p for p in self._selected_ids if p not in self._installed_ids]

        if not selected_not_installed:
            QMessageBox.warning(self, "No Selection", "No packages selected. Click checkboxes to select packages.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Bulk Installation",
            f"Install {len(selected_not_installed)} selected packages?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            total = len(selected_not_installed)

            self._set_progress(True, "Starting installation...", 0, total)
            QApplication.processEvents()

            successful = 0
            failed = 0

            # For NAI packages, we install one at a time (different from system packages)
            for idx, pkg_id in enumerate(selected_not_installed, 1):
                self._set_progress(True, f"Installing {pkg_id} ({idx}/{total})", idx-1, total)

                try:
                    process = subprocess.Popen(
                        ["nai", "install", pkg_id],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(timeout=120)

                    if process.returncode == 0:
                        successful += 1
                    else:
                        failed += 1
                        QMessageBox.warning(self, "Warning", f"Failed to install {pkg_id}\n{stderr[:100]}")
                except Exception as e:
                    failed += 1
                    QMessageBox.warning(self, "Warning", f"Failed to install {pkg_id}\n{str(e)}")

            self._set_progress(False)

            if failed == 0:
                QMessageBox.information(self, "Complete", f"Successfully installed {successful} packages!")
            else:
                QMessageBox.warning(self, "Partial Complete", f"Installed {successful} packages, {failed} failed.")

            self.refresh()

    def _uninstall_package(self, package_id: str):
        """Uninstall a package using nai uninstall CLI."""
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Uninstallation",
                f"Uninstall {package_id}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self._set_progress(True, f"Removing {package_id}...", 0, 0)

                process = subprocess.Popen(
                    ["nai", "uninstall", package_id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(timeout=120)

                self._set_progress(False)

                if process.returncode == 0:
                    QMessageBox.information(self, "Success", f"Uninstalled {package_id}")
                    self.refresh()
                else:
                    QMessageBox.critical(
                        self,
                        "Uninstallation Failed",
                        f"Failed to uninstall {package_id}:\n{stderr}"
                    )

        except subprocess.TimeoutExpired:
            self._set_progress(False)
            QMessageBox.critical(self, "Timeout", "Operation timed out")
        except Exception as e:
            self._set_progress(False)
            QMessageBox.critical(self, "Error", f"Operation failed:\n{str(e)}")

    def _uninstall_selected(self):
        """Uninstall all selected (installed) packages."""
        selected_installed = [p for p in self._selected_ids if p in self._installed_ids]

        if not selected_installed:
            QMessageBox.warning(self, "No Selection", "No installed packages selected.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Bulk Uninstallation",
            f"Uninstall {len(selected_installed)} selected packages?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            total = len(selected_installed)

            self._set_progress(True, "Starting uninstallation...", 0, total)
            QApplication.processEvents()

            successful = 0
            failed = 0

            for idx, pkg_id in enumerate(selected_installed, 1):
                self._set_progress(True, f"Uninstalling {pkg_id} ({idx}/{total})", idx-1, total)

                try:
                    process = subprocess.Popen(
                        ["nai", "uninstall", pkg_id],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(timeout=120)

                    if process.returncode == 0:
                        successful += 1
                    else:
                        failed += 1
                        QMessageBox.warning(self, "Warning", f"Failed to uninstall {pkg_id}\n{stderr[:100]}")
                except Exception as e:
                    failed += 1
                    QMessageBox.warning(self, "Warning", f"Failed to uninstall {pkg_id}\n{str(e)}")

            self._set_progress(False)

            if failed == 0:
                QMessageBox.information(self, "Complete", f"Successfully uninstalled {successful} packages!")
            else:
                QMessageBox.warning(self, "Partial Complete", f"Uninstalled {successful} packages, {failed} failed.")

            self.refresh()

    def _check_updates(self):
        """Check for available updates."""
        self._set_progress(True, "Checking for updates...", 0, 0)
        QMessageBox.information(
            self,
            "Check for Updates",
            "Checking for available updates...\n(NAI content package updates coming soon)"
        )
        self._set_progress(False)

class SettingsTabWidget(QWidget):
    """Tab for application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = Config()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        info = QLabel("Theme: Lumo Purple (fixed)")
        info.setStyleSheet("color: #888; font-size: 12px; font-style: italic;")
        layout.addWidget(info)

        github_label = QLabel("GitHub Configuration")
        github_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(github_label)

        github_form = QFormLayout()
        github_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.github_repo_input = QLineEdit(self._config.get("github_repo", ""))
        github_form.addRow("Repository:", self.github_repo_input)

        self.github_token_input = QLineEdit(self._config.get("github_token", ""))
        self.github_token_input.setEchoMode(QLineEdit.Password)
        github_form.addRow("Token:", self.github_token_input)

        layout.addLayout(github_form)

        paths_label = QLabel("Paths")
        paths_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 16px;")
        layout.addWidget(paths_label)

        content_layout = QHBoxLayout()
        content_layout.addWidget(QLabel("Content Path:"))
        self.content_path_input = QLineEdit(self._config.get("content_path", ""))
        content_layout.addWidget(self.content_path_input)
        self.content_path_browse = QPushButton("Browse...")
        self.content_path_browse.clicked.connect(lambda: self._browse_path(self.content_path_input))
        content_layout.addWidget(self.content_path_browse)
        layout.addLayout(content_layout)

        library_layout = QHBoxLayout()
        library_layout.addWidget(QLabel("Library Path:"))
        self.library_path_input = QLineEdit(self._config.get("library_path", ""))
        library_layout.addWidget(self.library_path_input)
        self.library_path_browse = QPushButton("Browse...")
        self.library_path_browse.clicked.connect(lambda: self._browse_path(self.library_path_input))
        library_layout.addWidget(self.library_path_browse)
        layout.addLayout(library_layout)

        install_layout = QHBoxLayout()
        install_layout.addWidget(QLabel("Install Path:"))
        self.install_path_input = QLineEdit(self._config.get("install_path", ""))
        install_layout.addWidget(self.install_path_input)
        layout.addLayout(install_layout)

        prefs_label = QLabel("Preferences")
        prefs_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 16px;")
        layout.addWidget(prefs_label)

        self.auto_update_checkbox = QCheckBox("Enable automatic updates")
        self.auto_update_checkbox.setChecked(self._config.get("auto_update", True))
        layout.addWidget(self.auto_update_checkbox)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._load_current_settings)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _browse_path(self, line_edit):
        """Open file dialog to select path."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            line_edit.text() or str(Path.home())
        )
        if directory:
            line_edit.setText(directory)

    def _save_settings(self):
        """Save current settings."""
        self._config.set("github_repo", self.github_repo_input.text())
        self._config.set("github_token", self.github_token_input.text())
        self._config.set("content_path", self.content_path_input.text())
        self._config.set("library_path", self.library_path_input.text())
        self._config.set("install_path", self.install_path_input.text())
        self._config.set("auto_update", self.auto_update_checkbox.isChecked())

        self._config.save()
        QMessageBox.information(self, "Settings Saved", "Configuration saved successfully.")

    def _load_current_settings(self):
        """Reload settings from current config."""
        self.github_repo_input.setText(self._config.get("github_repo", ""))
        self.github_token_input.setText(self._config.get("github_token", ""))
        self.content_path_input.setText(self._config.get("content_path", ""))
        self.library_path_input.setText(self._config.get("library_path", ""))
        self.install_path_input.setText(self._config.get("install_path", ""))
        self.auto_update_checkbox.setChecked(self._config.get("auto_update", True))

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nobara Audio Installer")
        self.setMinimumSize(900, 600)

        self._setup_menu_bar()
        self._setup_ui()
        self.statusBar().showMessage("Ready")

    def _setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")

        refresh_action = QAction("Refresh All", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_all)
        view_menu.addAction(refresh_action)

        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        """Set up the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()

        self.tabs.addTab(PackageBrowserWidget(), "Plugins")
        self.tabs.addTab(PackagesTabWidget(), "Packages")
        self.tabs.addTab(SettingsTabWidget(), "Settings")

        layout.addWidget(self.tabs)

    def _refresh_all(self):
        """Refresh all tabs."""
        plugin_tab = self.tabs.widget(0)
        if plugin_tab and hasattr(plugin_tab, 'refresh'):
            plugin_tab.refresh()

        packages_tab = self.tabs.widget(1)
        if packages_tab and hasattr(packages_tab, 'refresh'):
            packages_tab.refresh()

        self.statusBar().showMessage("Refreshed")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Nobara Audio Installer",
            "<b>Nobara Audio Installer</b><br>"
            "Version: 1.0.0<br><br>"
            "Manage audio production software and content on Nobara Linux.<br>"
            "Created by Willi Gunnz<br>"
            "July 2026"
        )
