"""Package browser widget for the GUI - shows DNF/COPR packages from list files."""

import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QScrollArea,
    QComboBox,
    QMessageBox,
    QProgressBar,
    QApplication,
)
from PyQt5.QtCore import Qt

from nai.config import get_config

# Import shared styles
from .styles import (
    PACKAGE_CARD_STYLE,
    INSTALL_BUTTON_STYLE,
    UNINSTALL_BUTTON_STYLE,
    SELECTED_BUTTON_STYLE,
    BULK_ACTION_BUTTON_STYLE,
    UPDATE_BUTTON_STYLE,
)

# Paths to list files
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGINS_LIST_DIR = PROJECT_ROOT / "plugins"

@dataclass
class PackageCard:
    """Data for displaying a package card."""
    name: str
    version: str
    arch: str
    summary: str
    reponame: str
    epoch: str
    release: str
    is_installed: bool = False
    is_selected: bool = False

class PackageBrowserWidget(QWidget):
    """Main package browser widget showing DNF/COPR packages from list files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = get_config()
        self._packages: List[PackageCard] = []
        self._selected_packages: set = set()
        self._installed_packages: set = set()

        self.content_widget = None
        self.content_layout = None
        self.scroll_area = None
        self.search_input = None
        self.category_combo = None
        self.info_label = None
        self.progress_status = None
        self.progress_bar = None

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()

        title = QLabel("Plugins")
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
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self._load_categories()
        filter_layout.addWidget(self.category_combo)

        filter_layout.addSpacing(16)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search plugins...")
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

    def _load_categories(self):
        """Load available category list files."""
        categories = ["all"]

        if PLUGINS_LIST_DIR.exists():
            for list_file in PLUGINS_LIST_DIR.glob("*.list"):
                category = list_file.stem
                if category != "my-plugins":
                    categories.append(category)

        self.category_combo.addItems(categories)

    def _read_package_list(self, category: str) -> List[str]:
        """Read package IDs from a category list file."""
        package_ids = []

        if category == "all":
            for list_file in PLUGINS_LIST_DIR.glob("*.list"):
                if list_file.stem != "my-plugins":
                    package_ids.extend(self._read_single_list(list_file))
            return list(dict.fromkeys(package_ids))

        list_file = PLUGINS_LIST_DIR / f"{category}.list"
        if list_file.exists():
            package_ids = self._read_single_list(list_file)

        return package_ids

    def _read_single_list(self, list_file: Path) -> List[str]:
        """Read package IDs from a single list file."""
        ids = []
        try:
            lines = list_file.read_text().strip().splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    ids.append(line)
        except IOError:
            pass
        return ids

    def _on_category_changed(self, category: str):
        """Handle category change."""
        self.refresh()

    def _on_search(self):
        """Handle search input."""
        query = self.search_input.text().lower()
        self._apply_filter(query)

    def refresh(self):
        """Refresh the package list from DNF/COPR sources."""
        if self.content_layout is None:
            return

        category = self.category_combo.currentText()
        package_ids = self._read_package_list(category)

        # Check each package individually using dnf5 list - MOST RELIABLE METHOD
        self._installed_packages = set()
        for pkg_name in package_ids:
            if self._is_package_installed_direct(pkg_name):
                self._installed_packages.add(pkg_name.lower())

        dnf_packages = self._query_dnf_packages(package_ids)

        self._packages = []
        for pkg_name, pkg_info in dnf_packages.items():
            is_installed = pkg_name.lower() in self._installed_packages

            card = PackageCard(
                name=pkg_name,
                version=pkg_info.get("version", "0"),
                arch=pkg_info.get("arch", "x86_64"),
                summary=pkg_info.get("summary", ""),
                reponame=pkg_info.get("reponame", ""),
                epoch=pkg_info.get("epoch", "0"),
                release=pkg_info.get("release", ""),
                is_installed=is_installed,
                is_selected=False,
            )
            self._packages.append(card)

        self._render_cards()

    def _is_package_installed_direct(self, package_name: str) -> bool:
        """Check if a SPECIFIC package is installed using dnf5 list. Most reliable method.

        Uses dnf5 list installed <package> which returns:
        - Exit code 0 = package found
        - Exit code 1 = package not found
        """
        try:
            result = subprocess.run(
                ["dnf5", "list", "installed", package_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            # dnf5 list returns 0 if found, 1 if not found
            if result.returncode == 0:
                return True
            else:
                return False

        except Exception as e:
            print(f"ERROR checking if {package_name} is installed: {e}")
            return False

    def _query_dnf_packages(self, package_names: List[str]) -> Dict[str, Dict[str, str]]:
        """Query DNF for package information."""
        packages = {}

        if not package_names:
            return packages

        for pkg_name in package_names:
            try:
                result = subprocess.run(
                    ["dnf5", "repoquery", "--qf", "%{name}|%{epoch}|%{version}|%{release}|%{arch}|%{summary}|%{reponame}", pkg_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split("|")
                    if len(parts) >= 7:
                        packages[pkg_name] = {
                            "name": parts[0],
                            "epoch": parts[1],
                            "version": parts[2],
                            "release": parts[3],
                            "arch": parts[4],
                            "summary": parts[5],
                            "reponame": parts[6],
                        }
            except Exception:
                pass

        return packages

    def _render_cards(self):
        """Render package cards in the UI."""
        if self.content_layout is None:
            return

        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        query = self.search_input.text().lower() if self.search_input else ""

        if query:
            filtered = [
                p for p in self._packages
                if query in p.name.lower()
                or query in p.summary.lower()
            ]
        else:
            filtered = self._packages

        if not filtered:
            msg = f"No packages found"
            if query:
                msg += f" matching '{query}'"

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
        installed = sum(1 for p in filtered if p.is_installed)
        selected = sum(1 for p in filtered if p.name in self._selected_packages)
        category = self.category_combo.currentText() if self.category_combo else "unknown"
        self.info_label.setText(
            f"Showing {shown} of {total} packages in '{category}' "
            f"({installed} installed, {selected} selected)"
        )

    def _create_package_card(self, pkg: PackageCard) -> QFrame:
        """Create a package card widget."""
        card = QFrame()
        card.setObjectName("packageCard")
        card.setStyleSheet(PACKAGE_CARD_STYLE)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        top_row = QHBoxLayout()

        is_selected = pkg.name in self._selected_packages
        select_checkbox = QPushButton("☑" if is_selected else "☐")
        select_checkbox.setFixedSize(32, 32)
        select_checkbox.setStyleSheet(SELECTED_BUTTON_STYLE if is_selected else BULK_ACTION_BUTTON_STYLE)
        select_checkbox.setToolTip("Include in bulk operations")
        select_checkbox.clicked.connect(lambda checked, name=pkg.name: self._toggle_selection(name))
        top_row.addWidget(select_checkbox)

        name_label = QLabel(f"<b>{pkg.name}</b>")
        name_label.setStyleSheet("font-size: 16px;")
        top_row.addWidget(name_label)

        top_row.addStretch()

        if pkg.is_installed:
            status_label = QLabel("✓ Installed")
            status_label.setStyleSheet("color: #4caf50; font-size: 13px;")
            top_row.addWidget(status_label)

            uninstall_btn = QPushButton("Uninstall")
            uninstall_btn.setFixedWidth(90)
            uninstall_btn.setStyleSheet(UNINSTALL_BUTTON_STYLE)
            uninstall_btn.clicked.connect(lambda checked: self._uninstall_package(pkg.name))
            top_row.addWidget(uninstall_btn)
        else:
            install_btn = QPushButton("Install")
            install_btn.setFixedWidth(90)
            install_btn.setStyleSheet(INSTALL_BUTTON_STYLE)
            install_btn.clicked.connect(lambda checked: self._install_package(pkg.name))
            top_row.addWidget(install_btn)

        layout.addLayout(top_row)

        meta_layout = QHBoxLayout()
        ver_label = QLabel(f"v{pkg.version}-{pkg.release}")
        ver_label.setStyleSheet("color: #aaa; font-size: 13px;")
        meta_layout.addWidget(ver_label)

        arch_label = QLabel(f"{pkg.arch} • {pkg.reponame}")
        arch_label.setStyleSheet("color: #888; font-size: 12px;")
        meta_layout.addWidget(arch_label)

        meta_layout.addStretch()
        layout.addLayout(meta_layout)

        if pkg.summary:
            desc_label = QLabel(pkg.summary)
            desc_label.setStyleSheet("color: #ccc; font-size: 13px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        return card

    def _toggle_selection(self, package_name: str):
        """Toggle selection status for a package."""
        if package_name in self._selected_packages:
            self._selected_packages.remove(package_name)
        else:
            self._selected_packages.add(package_name)

        self._render_cards()

    def _select_all(self):
        """Select all displayed packages."""
        if self.search_input:
            query = self.search_input.text().lower()
            if query:
                packages_to_select = [
                    p.name for p in self._packages
                    if query in p.name.lower() or query in p.summary.lower()
                ]
            else:
                packages_to_select = [p.name for p in self._packages]
        else:
            packages_to_select = [p.name for p in self._packages]

        self._selected_packages.update(packages_to_select)
        self._render_cards()

    def _unselect_all(self):
        """Unselect all packages."""
        self._selected_packages.clear()
        self._render_cards()

    def _install_package(self, package_name: str):
        """Install a SINGLE package using DNF with pkexec (GUI dialog)."""
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Installation",
                f"Install {package_name}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self._set_progress(True, f"Installing {package_name}...", 0, 0)

                process = subprocess.Popen(
                    ["pkexec", "dnf5", "install", "-y", package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate(timeout=60)

                # Wait for DNF to finalize
                time.sleep(2.0)
                QApplication.processEvents()

                # Force DNF cache refresh
                try:
                    subprocess.run(["dnf5", "makecache"], capture_output=True, timeout=30)
                except Exception:
                    pass

                time.sleep(0.5)
                QApplication.processEvents()

                self._set_progress(False)

                if process.returncode == 0:
                    is_now_installed = self._is_package_installed_direct(package_name)

                    if is_now_installed:
                        QMessageBox.information(self, "Success", f"Installed {package_name}")
                    else:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Install command succeeded, but DNF still reports {package_name} as not installed.\nTry refreshing manually."
                        )

                    self.refresh()
                else:
                    QMessageBox.critical(
                        self,
                        "Installation Failed",
                        f"Failed to install {package_name}:\n{stderr.decode()}"
                    )

        except subprocess.TimeoutExpired:
            self._set_progress(False)
            QMessageBox.critical(self, "Timeout", "Installation timed out")
        except Exception as e:
            self._set_progress(False)
            QMessageBox.critical(self, "Error", f"Installation failed:\n{str(e)}")

    def _uninstall_package(self, package_name: str):
        """Uninstall a SINGLE package using DNF with pkexec (GUI dialog)."""
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Uninstallation",
                f"Uninstall {package_name}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self._set_progress(True, f"Removing {package_name}...", 0, 0)

                process = subprocess.Popen(
                    ["pkexec", "dnf5", "remove", "-y", package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate(timeout=60)

                # WAIT LONGER for DNF to finalize database after uninstall
                time.sleep(2.0)
                QApplication.processEvents()

                # Force DNF cache refresh
                try:
                    subprocess.run(["dnf5", "makecache"], capture_output=True, timeout=30)
                except Exception:
                    pass

                time.sleep(0.5)
                QApplication.processEvents()

                self._set_progress(False)

                if process.returncode == 0:
                    is_still_installed = self._is_package_installed_direct(package_name)

                    if not is_still_installed:
                        QMessageBox.information(self, "Success", f"Uninstalled {package_name}")
                    else:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Uninstall command succeeded, but DNF still reports {package_name} as installed.\nTry refreshing manually."
                        )

                    self.refresh()
                else:
                    QMessageBox.critical(
                        self,
                        "Uninstallation Failed",
                        f"Failed to uninstall {package_name}:\n{stderr.decode()}"
                    )

        except subprocess.TimeoutExpired:
            self._set_progress(False)
            QMessageBox.critical(self, "Timeout", "Uninstallation timed out")
        except Exception as e:
            self._set_progress(False)
            QMessageBox.critical(self, "Error", f"Uninstallation failed:\n{str(e)}")

    def _install_selected(self):
        """Install all selected packages - ONE pkexec call with ALL packages (ONE GUI dialog)!"""
        if not self._selected_packages:
            QMessageBox.warning(self, "No Selection", "No packages selected. Click checkboxes to select packages.")
            return

        packages_to_install = [p for p in self._selected_packages if p not in self._installed_packages]
        if not packages_to_install:
            QMessageBox.information(self, "Nothing to Install", "All selected packages are already installed.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Bulk Installation",
            f"Install {len(packages_to_install)} selected packages?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            total = len(packages_to_install)

            self._set_progress(True, f"Installing {total} packages...", 0, total)
            QApplication.processEvents()

            try:
                process = subprocess.Popen(
                    ["pkexec", "dnf5", "install", "-y"] + packages_to_install,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                stdout, stderr = process.communicate(timeout=300)

                # Wait for DNF to finalize its database
                time.sleep(2.0)
                QApplication.processEvents()

                # Force DNF cache refresh
                try:
                    subprocess.run(["dnf5", "makecache"], capture_output=True, timeout=30)
                except Exception:
                    pass

                time.sleep(0.5)
                QApplication.processEvents()

                self._set_progress(False)
                QApplication.processEvents()

                if process.returncode == 0:
                    QMessageBox.information(self, "Complete", f"Successfully installed {total} packages!")
                else:
                    QMessageBox.warning(
                        self,
                        "Partial Complete",
                        f"Some packages may have failed.\nOutput:\n{stdout.decode()[:500]}"
                    )

                QApplication.processEvents()

                self.refresh()

                QApplication.processEvents()

            except subprocess.TimeoutExpired:
                process.kill()
                self._set_progress(False)
                QApplication.processEvents()
                QMessageBox.critical(self, "Timeout", "Installation timed out")
            except Exception as e:
                self._set_progress(False)
                QApplication.processEvents()
                QMessageBox.critical(self, "Error", f"Installation failed:\n{str(e)}")

    def _uninstall_selected(self):
        """Uninstall all selected (installed) packages - ONE pkexec call with ALL packages!"""
        selected_installed = [p for p in self._selected_packages if p in self._installed_packages]

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

            self._set_progress(True, f"Uninstalling {total} packages...", 0, total)
            QApplication.processEvents()

            try:
                process = subprocess.Popen(
                    ["pkexec", "dnf5", "remove", "-y"] + selected_installed,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                stdout, stderr = process.communicate(timeout=300)

                # WAIT LONGER for DNF to finalize database after uninstall
                time.sleep(3.0)
                QApplication.processEvents()

                # Force DNF cache refresh
                try:
                    subprocess.run(["dnf5", "makecache"], capture_output=True, timeout=30)
                except Exception:
                    pass

                time.sleep(0.5)
                QApplication.processEvents()

                self._set_progress(False)
                QApplication.processEvents()

                if process.returncode == 0:
                    # Verify at least some were removed
                    still_installed_count = 0
                    for pkg in selected_installed:
                        if self._is_package_installed_direct(pkg):
                            still_installed_count += 1

                    if still_installed_count == 0:
                        QMessageBox.information(self, "Complete", f"Successfully uninstalled {total} packages!")
                    elif still_installed_count == total:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Uninstall completed but DNF still reports all {total} packages as installed.\nTry refreshing manually."
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Partial Complete",
                            f"Removed {total - still_installed_count} of {total} packages.\n{still_installed_count} still show as installed."
                        )
                else:
                    QMessageBox.warning(
                        self,
                        "Partial Complete",
                        f"Some packages may have failed.\nOutput:\n{stdout.decode()[:500]}"
                    )

                QApplication.processEvents()

                self.refresh()

                QApplication.processEvents()

            except subprocess.TimeoutExpired:
                process.kill()
                self._set_progress(False)
                QApplication.processEvents()
                QMessageBox.critical(self, "Timeout", "Uninstallation timed out")
            except Exception as e:
                self._set_progress(False)
                QApplication.processEvents()
                QMessageBox.critical(self, "Error", f"Uninstallation failed:\n{str(e)}")

    def _check_updates(self):
        """Check for available updates."""
        try:
            self._set_progress(True, "Checking for updates...", 0, 0)

            process = subprocess.Popen(
                ["pkexec", "dnf5", "check-update"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=120)

            self._set_progress(False)

            if process.returncode == 1:
                lines = stdout.decode().strip().split("\n")
                update_count = len([l for l in lines if l and not l.startswith("Package")])
                QMessageBox.information(self, "Updates Available", f"{update_count} updates found.\nRun 'dnf5 upgrade' to install them.")
            else:
                QMessageBox.information(self, "Up to Date", "No updates available.")

        except subprocess.TimeoutExpired:
            self._set_progress(False)
            QMessageBox.warning(self, "Timeout", "Update check timed out")
        except Exception as e:
            self._set_progress(False)
            QMessageBox.warning(self, "Error", f"Update check failed:\n{str(e)}")

    def _apply_filter(self, query: str):
        """Apply search filter."""
        self._render_cards()
