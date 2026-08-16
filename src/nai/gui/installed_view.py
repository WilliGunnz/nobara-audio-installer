"""View for managing installed packages."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QMenu, QCheckBox,
)


class ActionButton(QLabel):
    """Custom QLabel styled and clickable like a button."""

    clicked = pyqtSignal()

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                background-color: #3d0c5c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-size: 15px;
                font-weight: bold;
            }
            QLabel:hover {
                background-color: #6d4aff;
            }
            QLabel:pressed {
                background-color: #270040;
            }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                background-color: #6d4aff;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-size: 15px;
                font-weight: bold;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                background-color: #3d0c5c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-size: 15px;
                font-weight: bold;
            }
        """)
        super().leaveEvent(event)


class InstalledPackagesWidget(QWidget):
    """Widget for viewing and managing installed packages."""

    uninstall_requested = pyqtSignal(str)
    batch_uninstall_requested = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header row
        header_layout = QHBoxLayout()

        title_label = QLabel("Installed Packages")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)

        update_all_btn = QPushButton("Check Updates")
        update_all_btn.clicked.connect(self._check_updates)
        header_layout.addWidget(update_all_btn)

        # Batch action buttons
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        header_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        header_layout.addWidget(deselect_all_btn)

        batch_uninstall_btn = QPushButton("Uninstall Selected")
        batch_uninstall_btn.setMinimumWidth(150)
        batch_uninstall_btn.clicked.connect(self._on_batch_uninstall)
        header_layout.addWidget(batch_uninstall_btn)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Select", "Package ID", "Name", "Version", "Category", "Actions"
        ])

        # Set specific column widths and resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 75)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 160)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setAlternatingRowColors(False)
        self.table.setMinimumHeight(300)

        layout.addWidget(self.table)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def _select_all(self):
        """Check all visible checkboxes."""
        for row in range(self.table.rowCount()):
            cb_container = self.table.cellWidget(row, 0)
            if cb_container:
                cbs = cb_container.findChildren(QCheckBox)
                if cbs:
                    cbs[0].setChecked(True)

    def _deselect_all(self):
        """Uncheck all visible checkboxes."""
        for row in range(self.table.rowCount()):
            cb_container = self.table.cellWidget(row, 0)
            if cb_container:
                cbs = cb_container.findChildren(QCheckBox)
                if cbs:
                    cbs[0].setChecked(False)

    def _get_selected_package_ids(self) -> list[str]:
        """Get list of all checked package IDs."""
        selected = []
        for row in range(self.table.rowCount()):
            cb_container = self.table.cellWidget(row, 0)
            if cb_container:
                cbs = cb_container.findChildren(QCheckBox)
                if cbs and cbs[0].isChecked():
                    pkg_id = self.table.item(row, 1).text()
                    selected.append(pkg_id)
        return selected

    def _update_selection_label(self, count: int):
        """Update the selection count label."""
        if count > 0:
            self.status_label.setText(f"{count} package(s) selected for uninstall")
            self.status_label.setStyleSheet("color: #6d4aff;")
        elif self.table.rowCount() == 0:
            self.status_label.setText("No packages installed. Browse to find packages!")
            self.status_label.setStyleSheet("color: #808080;")
        else:
            self.status_label.setText(f"{self.table.rowCount()} package(s) installed")
            self.status_label.setStyleSheet("color: #6d4aff;")

    def refresh(self):
        """Reload installed packages."""
        from nai.installer import list_installed

        installed = list_installed()
        self.table.setRowCount(len(installed))

        for row, pkg in enumerate(installed):
            # Checkbox column - wrapped in a container widget for centering
            checkbox_container = QWidget()
            checkbox_container.setStyleSheet("background-color: transparent;")
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setSpacing(0)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            checkbox = QCheckBox()
            checkbox.setProperty("package_id", pkg.get("package_id", ""))
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #6d4aff;
                    border-radius: 3px;
                    background-color: #1a1a1a;
                }
                QCheckBox::indicator:checked {
                    background-color: #6d4aff;
                    border: 2px solid #6d4aff;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #8f6aff;
                }
            """)
            checkbox_layout.addWidget(checkbox)
            self.table.setCellWidget(row, 0, checkbox_container)

            # Package ID
            id_item = QTableWidgetItem(pkg.get("package_id", "?"))
            id_item.setForeground(Qt.GlobalColor.white)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 1, id_item)

            # Name
            name_item = QTableWidgetItem(pkg.get("name", "Unknown"))
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 2, name_item)

            # Version
            ver_item = QTableWidgetItem(f"v{pkg.get('version', '?')}")
            ver_item.setForeground(Qt.GlobalColor.white)
            ver_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 3, ver_item)

            # Category
            cat_item = QTableWidgetItem(pkg.get("category", "?"))
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 4, cat_item)

            # Actions button
            actions_widget = QWidget()
            actions_widget.setStyleSheet("background-color: transparent;")
            actions_layout = QVBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            actions_layout.setSpacing(0)

            uninstall_btn = ActionButton("Uninstall")
            uninstall_btn.setProperty("package_id", pkg.get("package_id", ""))
            uninstall_btn.clicked.connect(self._on_uninstall_clicked)

            actions_layout.addWidget(uninstall_btn, alignment=Qt.AlignmentFlag.AlignCenter)

            self.table.setCellWidget(row, 5, actions_widget)

        self._update_selection_label(len(installed))

    def _on_batch_uninstall(self):
        """Handle batch uninstall button click."""
        selected = self._get_selected_package_ids()
        if selected:
            reply = QMessageBox.question(
                self,
                "Confirm Batch Uninstall",
                f"Are you sure you want to uninstall {len(selected)} package(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.batch_uninstall_requested.emit(selected)
                for row in range(self.table.rowCount()):
                    cb_container = self.table.cellWidget(row, 0)
                    if cb_container:
                        cbs = cb_container.findChildren(QCheckBox)
                        if cbs:
                            cbs[0].setChecked(False)
                self._update_selection_label(0)

    def _on_uninstall_clicked(self):
        """Handle individual uninstall button click."""
        sender = self.sender()
        package_id = sender.property("package_id")

        reply = QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall '{package_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            from nai.installer import uninstall_package, InstallError

            try:
                uninstall_package(package_id)

                try:
                    self.window().statusBar().showMessage(f"✓ Uninstalled: {package_id}")
                except Exception:
                    pass

                self.refresh()
            except InstallError as e:
                QMessageBox.critical(self, "Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Unexpected Error", f"Failed to uninstall: {e}")

    def _check_updates(self):
        """Check for package updates."""
        from nai.installer import check_for_updates

        updates = check_for_updates()

        if not updates:
            QMessageBox.information(self, "Updates", "All packages are up to date!")
            return

        msg = "Updates available:\n\n"
        for upd in updates:
            msg += f"• {upd['package_id']}: v{upd['current_version']} → v{upd['latest_version']}\n"

        QMessageBox.information(self, "Updates Available", msg)

    def _show_context_menu(self, pos):
        """Show context menu on right-click."""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        package_id = self.table.item(row, 1).text()

        menu = QMenu()
        uninstall_action = QAction("Uninstall", menu)
        uninstall_action.triggered.connect(lambda: self._uninstall_selected())
        menu.addAction(uninstall_action)

        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def _uninstall_selected(self):
        """Uninstall selected package."""
        row = self.table.currentRow()
        if row < 0:
            return

        package_id = self.table.item(row, 1).text()
        self._on_uninstall_clicked()

    def statusBar(self):
        """Safely get parent status bar."""
        try:
            return self.window().statusBar()
        except Exception:
            return None
