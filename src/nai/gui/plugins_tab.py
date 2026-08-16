"""Plugins tab widget for browsing and installing system packages."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QScrollArea, QLabel,
    QFrame, QSizePolicy, QMessageBox, QComboBox,
    QCheckBox,
)

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Runtime import for type checking (with circular import protection)
if TYPE_CHECKING:
    from nai.gui.main_window import MainWindow

logger = logging.getLogger(__name__)

class PluginCard(QFrame):
    """Individual plugin package card."""

    install_clicked = pyqtSignal(str, str, str)
    update_clicked = pyqtSignal(str, str, str)

    def __init__(self, package_data: dict):
        super().__init__()
        self.package_data = package_data
        self._has_update = package_data.get("has_update", False)
        self._update_info = package_data.get("update_info", {})
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("PluginCard")
        self.setStyleSheet("""
            QFrame#PluginCard {
                background-color: #2a2a2a;
                border: 1px solid #3d0c5c;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame#PluginCard:hover {
                border: 2px solid #6d4aff;
            }
            QFrame#PluginCard.has-update {
                border: 2px solid #ff6b00;
                background-color: #2d2520;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        name_label = QLabel(self.package_data.get("name", "Unknown"))
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")

        if self._has_update:
            update_badge = QLabel("↑ UPDATE AVAILABLE")
            update_badge.setStyleSheet(
                "background-color: #ff6b00; "
                "color: white; "
                "padding: 2px 8px; "
                "border-radius: 4px; "
                "font-size: 10px; "
                "font-weight: bold;"
            )
            header_layout.addWidget(update_badge)

        header_layout.addWidget(name_label)

        source = self.package_data.get("source", "unknown")
        badge_text = "📦 COPR" if source == "copr" else "📦 DNF"
        badge_label = QLabel(badge_text)
        badge_label.setStyleSheet(
            "background-color: #3d0c5c; "
            "color: #ffffff; "
            "padding: 2px 8px; "
            "border-radius: 4px; "
            "font-size: 11px;"
        )
        header_layout.addWidget(badge_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        summary = self.package_data.get("summary", "No description available")
        summary_label = QLabel(summary)
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("color: #b0b0b0; font-size: 12px;")
        summary_label.setMaximumHeight(60)
        layout.addWidget(summary_label)

        footer_layout = QHBoxLayout()
        version = self.package_data.get("full_version", "")
        repo_id = self.package_data.get("repo_id", "")

        version_label = QLabel(version)
        version_label.setStyleSheet("color: #808080; font-size: 11px;")
        footer_layout.addWidget(version_label)

        footer_layout.addStretch()

        repo_label = QLabel(repo_id)
        repo_label.setStyleSheet("color: #6d4aff; font-size: 11px;")
        footer_layout.addWidget(repo_label)
        layout.addLayout(footer_layout)

        if self._has_update and self._update_info:
            update_layout = QHBoxLayout()
            current_ver = self._update_info.get("current_version", "")
            available_ver = self._update_info.get("available_version", "")

            update_label = QLabel(f"Current: {current_ver} → Available: {available_ver}")
            update_label.setStyleSheet("color: #ff6b00; font-size: 10px; font-style: italic;")
            update_layout.addWidget(update_label)
            update_layout.addStretch()
            layout.addLayout(update_layout)

        button_layout = QHBoxLayout()

        if self._has_update:
            self.action_btn = QPushButton("↑ Update")
            self.action_btn.setToolTip(f"Update to {self._update_info.get('available_version', '')}")
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff6b00;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e55a00;
                }
            """)
            self.action_btn.clicked.connect(self._on_update_click)
        else:
            self.action_btn = QPushButton("Install")
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6d4aff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a3ddb;
                }
            """)
            self.action_btn.clicked.connect(self._on_install_click)

        self.action_btn.setFixedWidth(100)
        button_layout.addWidget(self.action_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _on_install_click(self):
        name = self.package_data.get("name", "")
        source = self.package_data.get("source", "").upper()
        repo_id = self.package_data.get("repo_id", "")
        self.install_clicked.emit(name, source, repo_id)

    def _on_update_click(self):
        name = self.package_data.get("name", "")
        source = self.package_data.get("source", "").upper()
        repo_id = self.package_data.get("repo_id", "")
        self.update_clicked.emit(name, source, repo_id)

    def set_has_update(self, has_update: bool, update_info: dict | None = None):
        self._has_update = has_update
        self._update_info = update_info or {}
        self._setup_ui()

    def set_package_data(self, package_data: dict):
        self.package_data = package_data
        self._has_update = package_data.get("has_update", False)
        self._update_info = package_data.get("update_info", {})
        self._setup_ui()

class PluginsTabWidget(QWidget):
    """Main plugins tab container."""

    plugin_install_requested = pyqtSignal(str, str, str)
    plugin_update_requested = pyqtSignal(str, str, str)
    plugin_search_requested = pyqtSignal(str)
    sources_initialized = pyqtSignal()
    updates_checked = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._current_results: list[dict] = []
        self._update_cache: dict[str, dict] = {}
        self._auto_check_enabled = True
        self._awaiting_update_check = False

        print("=== PluginsTabWidget.__init__ called ===")
        self.updates_checked.connect(self._on_updates_received)

        self._setup_ui()
        print("=== PluginsTabWidget setup complete ===")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search for plugins (e.g., ardour, vcvrack)...")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3d0c5c;
                border-radius: 4px;
                padding: 0 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #6d4aff;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.auto_check_cb = QCheckBox("Auto-check updates")
        self.auto_check_cb.setChecked(True)
        self.auto_check_cb.setStyleSheet("color: #808080; font-size: 11px;")
        self.auto_check_cb.stateChanged.connect(self._on_auto_check_toggle)
        filter_row.addWidget(self.auto_check_cb)

        self.source_filter = QComboBox()
        self.source_filter.addItems([
            "All Sources",
            "COPR (audinux)",
            "DNF (System)",
            "Has Updates Only"
        ])
        self.source_filter.setFixedHeight(32)
        self.source_filter.setFixedWidth(150)
        self.source_filter.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3d0c5c;
                border-radius: 4px;
                padding: 0 8px;
            }
        """)
        self.source_filter.currentIndexChanged.connect(self._on_filter_change)
        filter_row.addWidget(self.source_filter)

        self.refresh_btn = QPushButton("⟳ Refresh")
        self.refresh_btn.setFixedHeight(32)
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d0c5c;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a1c7c;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_packages)
        filter_row.addWidget(self.refresh_btn)

        header_layout.addLayout(filter_row)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.update_banner = QLabel("")
        self.update_banner.setVisible(False)
        self.update_banner.setStyleSheet("""
            QLabel {
                background-color: #ff6b00;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.update_banner)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; }")

        scroll_contents = QWidget()
        self.scroll_layout = QGridLayout(scroll_contents)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setColumnStretch(0, 1)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(scroll_contents)
        layout.addWidget(self.scroll_area)

        self.result_count_label = QLabel("Showing 0 plugins")
        self.result_count_label.setStyleSheet("color: #808080; font-size: 12px;")
        layout.addWidget(self.result_count_label)

        self.sources_initialized.connect(self._on_sources_ready)

    def _on_search(self):
        query = self.search_input.text().strip()
        if query:
            self.plugin_search_requested.emit(query)
            self.refresh_packages()

    def _on_auto_check_toggle(self):
        self._auto_check_enabled = self.auto_check_cb.isChecked()
        if self._auto_check_enabled:
            self._check_for_updates_async()

    def _on_filter_change(self):
        self.refresh_packages()

    def _on_sources_ready(self):
        print("=== _on_sources_ready called ===")
        self._awaiting_update_check = True
        self._show_empty_state("Checking for updates...")
        self._check_for_updates_async()

    def _check_for_updates_async(self):
        """Check for updates in a background thread."""
        import threading
        from nai.installer.update_checker import get_available_updates, UpdateInfo

        print("=== Starting update check ===")

        def check_updates():
            try:
                updates = get_available_updates()
                print(f"Got {len(updates)} updates from checker")

                self._update_cache.clear()
                for update_info in updates:
                    if isinstance(update_info, UpdateInfo):
                        pkg_id = update_info.package_id
                        current_ver = update_info.current_version
                        available_ver = update_info.available_version
                        repo_id = getattr(update_info, 'repo_id', '')
                        source_type = getattr(update_info, 'source_type', '')
                    else:
                        pkg_id = update_info.get('package_id')
                        current_ver = update_info.get('current_version', '')
                        available_ver = update_info.get('available_version', '')
                        repo_id = update_info.get('repo_id', '')
                        source_type = update_info.get('source_type', '')

                    self._update_cache[pkg_id] = {
                        "package_id": pkg_id,
                        "current_version": current_ver,
                        "available_version": available_ver,
                        "repo_id": repo_id,
                        "source_type": source_type,
                    }
                    print(f"Cached update for: {pkg_id}")

                print(f"Update cache now has {len(self._update_cache)} entries")
                print(f"Cache keys: {list(self._update_cache.keys())}")
                self.updates_checked.emit(list(self._update_cache.values()))

            except Exception as e:
                print(f"Update check failed: {e}")
                import traceback
                traceback.print_exc()

        thread = threading.Thread(target=check_updates, daemon=True)
        thread.start()

    def _on_updates_received(self, updates_list):
        """Called on main thread when updates check completes."""
        print(f"=== Updates received on main thread: {len(updates_list)} updates ===")
        print(f"Update cache keys: {list(self._update_cache.keys())}")

        self._awaiting_update_check = False
        self.refresh_packages()

    def refresh_packages(self, search_query: str = ""):
        print(f"refresh_packages called, cache size: {len(self._update_cache)}")

        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not search_query:
            search_query = self.search_input.text().strip()

        main_window = self.window()

        if not main_window or not hasattr(main_window, 'get_source_manager'):
            print("MainWindow not initialized yet, skipping refresh")
            self._show_empty_state("Initializing...")
            return

        source_manager = main_window.get_source_manager()
        if not source_manager:
            print("Package sources still loading...")
            self._show_empty_state("Package sources still loading...")
            return

        filter_index = self.source_filter.currentIndex()
        source_arg = None
        has_updates_only = False

        if filter_index == 1:
            source_arg = "audinux"
        elif filter_index == 2:
            source_arg = "dnf"
        elif filter_index == 3:
            has_updates_only = True

        try:
            if search_query:
                print(f"Searching for: {search_query}")
                results = source_manager.search(search_query, source=source_arg)
            else:
                # Try searching for common terms instead of hardcoded packages
                search_terms = ["audio", "music", "jack", "pulse", "ladle"]
                results = []

                print(f"Trying search terms: {search_terms}")
                for term in search_terms:
                    try:
                        term_results = source_manager.search(term, source=source_arg)
                        print(f"Found {len(term_results)} packages for '{term}'")
                        results.extend(term_results[:3])  # Take first 3 from each
                    except Exception as e:
                        print(f"Search for '{term}' failed: {e}")

                print(f"Total results: {len(results)}")

                # Remove duplicates by package name
                seen = set()
                unique_results = []
                for pkg in results:
                    if pkg.name not in seen:
                        seen.add(pkg.name)
                        unique_results.append(pkg)
                results = unique_results
                print(f"Unique results: {len(results)}")

        except Exception as e:
            print(f"Failed to search plugins: {e}")
            import traceback
            traceback.print_exc()
            self._show_empty_state(f"Error searching: {e}")
            return

        print(f"Found {len(results)} packages from source manager")

        if has_updates_only:
            results = [p for p in results if p.name in self._update_cache]
            if not results:
                self._show_empty_state("No plugins with available updates")
                return

        enhanced_results = []
        for pkg in results:
            update_info = self._update_cache.get(pkg.name)
            has_update = update_info is not None

            print(f"Package {pkg.name} - has_update={has_update}, cache key match: {pkg.name in self._update_cache}")

            enhanced_results.append({
                "name": pkg.name,
                "full_version": pkg.full_version,
                "summary": pkg.summary,
                "repo_id": pkg.repo_id,
                "source": pkg.source.value,
                "has_update": has_update,
                "update_info": update_info if has_update else {},
            })

        self._current_results = enhanced_results
        self._render_cards(enhanced_results)
        self._update_banner_from_cache()

    def _update_banner_from_cache(self):
        if self._update_cache:
            count = len(self._update_cache)
            self.update_banner.setText(f"✨ {count} update(s) available!")
            self.update_banner.setVisible(True)
        else:
            self.update_banner.setText("✨ All plugins are up to date!")
            self.update_banner.setVisible(True)
            QTimer.singleShot(3000, lambda: self.update_banner.setVisible(False))

    def _render_cards(self, packages):
        print(f"_render_cards called with {len(packages)} packages")

        if not packages:
            print("No packages to render")
            self._show_empty_state("No plugins found")
            return

        self.result_count_label.setText(f"Showing {len(packages)} plugin(s)")

        col = 0
        max_cols = 2
        row = 0

        for pkg in packages:
            card = PluginCard(pkg)

            card.install_clicked.connect(self.plugin_install_requested.emit)
            card.update_clicked.connect(self.plugin_update_requested.emit)

            self.scroll_layout.addWidget(card, row, col)
            col += 1

            if col >= max_cols:
                col = 0
                row += 1

    def _show_empty_state(self, message: str):
        self.result_count_label.setText("0 plugins")
        self.update_banner.setVisible(False)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(message)
        label.setStyleSheet("color: #808080; font-size: 14px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(label)

        self.scroll_layout.addWidget(center_widget, 0, 0, 1, 2)

    def set_auto_check_enabled(self, enabled: bool):
        self._auto_check_enabled = enabled
        self.auto_check_cb.setChecked(enabled)
        if enabled:
            self._check_for_updates_async()
