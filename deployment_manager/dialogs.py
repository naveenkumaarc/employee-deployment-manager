from __future__ import annotations

import sqlite3
from typing import Any

from PySide6.QtCore import QDate, QSize, Qt, QTime
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .theme import COLORS
from .widgets import (
    AdaptiveComboBox,
    WheelSafeDoubleSpinBox,
    WheelSafeTimeEdit,
    format_currency,
    make_button,
    make_date_edit,
    make_table,
    set_combo_value,
)

EMPLOYEE_COLORS = [
    ("Pastel rose", "#D86F78"),
    ("Coral", "#E9858D"),
    ("Teal", "#19B8A4"),
    ("Amber", "#F3A83B"),
    ("Violet", "#8B5CF6"),
    ("Sky", "#2E9BEF"),
    ("Rose", "#E85583"),
    ("Green", "#3BA272"),
]

MASTER_TITLES = {
    "employee": "Employee",
    "customer": "Customer",
    "project": "Project",
    "site": "Site",
}

MASTER_COLUMNS = {
    "employee": ["Code", "Employee", "Designation", "Phone", "Status"],
    "customer": ["Customer", "Contact person", "Phone", "Address", "Status"],
    "project": ["Code", "Project", "Customer", "Description", "Status"],
    "site": ["Site", "Customer", "City", "Address", "Status"],
}


def _plain_label(text: str, *, muted: bool = False) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    if muted:
        label.setObjectName("Muted")
    return label


class MasterEditorDialog(QDialog):
    def __init__(
        self,
        database: Database,
        entity: str,
        record_id: int | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.database = database
        self.entity = entity
        self.record_id = record_id
        self.record = (
            database.get_master(entity, record_id) if record_id is not None else None
        )
        title = f"{'Edit' if self.record else 'Add'} {MASTER_TITLES[entity]}"
        self.setWindowTitle(title)
        self.resize(570, 570)
        self.setMinimumSize(500, 430)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        heading = QLabel(title)
        heading.setObjectName("PageTitle")
        outer.addWidget(heading)
        help_text = QLabel("Fields marked with * are required.")
        help_text.setObjectName("Muted")
        outer.addWidget(help_text)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        self.form = QFormLayout(body)
        self.form.setContentsMargins(4, 12, 12, 12)
        self.form.setHorizontalSpacing(18)
        self.form.setVerticalSpacing(13)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        self.fields: dict[str, QWidget] = {}
        self._build_fields()

        self.active = QCheckBox("Active and available for new deployments")
        self.active.setChecked(bool(self.record.get("active", 1)) if self.record else True)
        self.form.addRow("", self.active)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("Primary")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        if self.record:
            self._load_record()

    def _line(self, placeholder: str = "") -> QLineEdit:
        widget = QLineEdit()
        widget.setPlaceholderText(placeholder)
        return widget

    def _text(self, placeholder: str = "") -> QPlainTextEdit:
        widget = QPlainTextEdit()
        widget.setPlaceholderText(placeholder)
        widget.setMaximumHeight(95)
        return widget

    def _customer_combo(self) -> QComboBox:
        combo = AdaptiveComboBox()
        combo.addItem("Select customer", None)
        for row in self.database.list_master("customer", active_only=False):
            suffix = "" if row["active"] else " (inactive)"
            combo.addItem(row["name"] + suffix, row["id"])
        return combo

    def _build_fields(self) -> None:
        if self.entity == "employee":
            specs = (
                ("employee_code", "Employee code", self._line("Optional internal code")),
                ("name", "Employee name *", self._line("Full name")),
                ("designation", "Designation", self._line("e.g. Electrical Technician")),
                ("phone", "Phone", self._line()),
                ("email", "Email", self._line()),
            )
            for key, label, widget in specs:
                self.fields[key] = widget
                self.form.addRow(label, widget)
            color = AdaptiveComboBox()
            for name, value in EMPLOYEE_COLORS:
                color.addItem(name, value)
                index = color.count() - 1
                color.setItemData(index, QColor(value), Qt.ItemDataRole.DecorationRole)
            self.fields["color"] = color
            self.form.addRow("Calendar colour", color)

        elif self.entity == "customer":
            specs = (
                ("name", "Customer name *", self._line("Company name")),
                ("contact_person", "Contact person", self._line()),
                ("phone", "Phone", self._line()),
                ("email", "Email", self._line()),
                ("address", "Address", self._text()),
            )
            for key, label, widget in specs:
                self.fields[key] = widget
                self.form.addRow(label, widget)

        elif self.entity == "project":
            customer = self._customer_combo()
            self.fields["customer_id"] = customer
            self.form.addRow("Customer *", customer)
            specs = (
                ("project_code", "Project code", self._line("Optional job/order code")),
                ("name", "Project name *", self._line()),
                ("description", "Description", self._text()),
            )
            for key, label, widget in specs:
                self.fields[key] = widget
                self.form.addRow(label, widget)

        elif self.entity == "site":
            customer = self._customer_combo()
            self.fields["customer_id"] = customer
            self.form.addRow("Customer *", customer)
            specs = (
                ("name", "Site name *", self._line("Plant, unit or facility")),
                ("city", "City / location", self._line()),
                ("address", "Address", self._text()),
            )
            for key, label, widget in specs:
                self.fields[key] = widget
                self.form.addRow(label, widget)

    def _load_record(self) -> None:
        assert self.record is not None
        for key, widget in self.fields.items():
            value = self.record.get(key)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value or ""))
            elif isinstance(widget, QPlainTextEdit):
                widget.setPlainText(str(value or ""))
            elif isinstance(widget, QComboBox):
                set_combo_value(widget, value)

    def _values(self) -> dict[str, Any]:
        result: dict[str, Any] = {"active": self.active.isChecked()}
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                result[key] = widget.text().strip()
            elif isinstance(widget, QPlainTextEdit):
                result[key] = widget.toPlainText().strip()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentData()
        return result

    def _save(self) -> None:
        try:
            self.database.save_master(self.entity, self._values(), self.record_id)
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Duplicate record",
                "A record with the same name or code already exists.",
            )
            return
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot save", str(exc))
            return
        self.accept()


class MasterTab(QWidget):
    def __init__(self, database: Database, entity: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.database = database
        self.entity = entity
        self.rows: dict[int, dict[str, Any]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(10)

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(f"Search {MASTER_TITLES[entity].lower()}s")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        controls.addWidget(self.search, 1)

        add_button = make_button(f"Add {MASTER_TITLES[entity]}", role="Primary")
        edit_button = make_button("Edit")
        self.toggle_button = make_button("Deactivate", role="Danger")
        add_button.clicked.connect(self.add_record)
        edit_button.clicked.connect(self.edit_record)
        self.toggle_button.clicked.connect(self.toggle_record)
        controls.addWidget(add_button)
        controls.addWidget(edit_button)
        controls.addWidget(self.toggle_button)
        layout.addLayout(controls)

        self.table = make_table(MASTER_COLUMNS[entity])
        self.table.itemSelectionChanged.connect(self._sync_toggle_text)
        self.table.doubleClicked.connect(lambda _index: self.edit_record())
        layout.addWidget(self.table, 1)
        self.refresh()

    def _display_values(self, row: dict[str, Any]) -> list[str]:
        status = "Active" if row["active"] else "Inactive"
        if self.entity == "employee":
            return [
                row.get("employee_code") or "",
                row["name"],
                row.get("designation") or "",
                row.get("phone") or "",
                status,
            ]
        if self.entity == "customer":
            return [
                row["name"],
                row.get("contact_person") or "",
                row.get("phone") or "",
                row.get("address") or "",
                status,
            ]
        if self.entity == "project":
            return [
                row.get("project_code") or "",
                row["name"],
                row.get("customer_name") or "",
                row.get("description") or "",
                status,
            ]
        return [
            row["name"],
            row.get("customer_name") or "",
            row.get("city") or "",
            row.get("address") or "",
            status,
        ]

    def selected_id(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        item = self.table.item(selected[0].row(), 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def refresh(self) -> None:
        needle = self.search.text().strip().casefold()
        rows = self.database.list_master(self.entity, active_only=False)
        if needle:
            rows = [
                row
                for row in rows
                if needle in " ".join(str(value or "") for value in row.values()).casefold()
            ]
        self.rows = {int(row["id"]): row for row in rows}
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = self._display_values(row)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row["id"])
                if not row["active"]:
                    item.setForeground(QColor(COLORS["muted"]))
                self.table.setItem(row_index, column, item)
        self.table.resizeRowsToContents()
        self._sync_toggle_text()

    def add_record(self) -> None:
        if MasterEditorDialog(self.database, self.entity, parent=self).exec():
            self.refresh()

    def edit_record(self) -> None:
        record_id = self.selected_id()
        if record_id is None:
            QMessageBox.information(self, "Select a record", "Select a row to edit.")
            return
        if MasterEditorDialog(
            self.database, self.entity, record_id=record_id, parent=self
        ).exec():
            self.refresh()

    def _sync_toggle_text(self) -> None:
        record_id = self.selected_id()
        active = self.rows.get(record_id, {}).get("active", 1)
        self.toggle_button.setText("Deactivate" if active else "Reactivate")
        self.toggle_button.setObjectName("Danger" if active else "Primary")
        self.toggle_button.style().unpolish(self.toggle_button)
        self.toggle_button.style().polish(self.toggle_button)

    def toggle_record(self) -> None:
        record_id = self.selected_id()
        if record_id is None:
            QMessageBox.information(self, "Select a record", "Select a row first.")
            return
        active = bool(self.rows[record_id]["active"])
        action = "deactivate" if active else "reactivate"
        if active:
            answer = QMessageBox.question(
                self,
                "Deactivate record",
                f"New deployments will no longer offer this {self.entity}. "
                "Existing history will remain unchanged.\n\nContinue?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.database.set_master_active(self.entity, record_id, not active)
        self.refresh()


class DirectoryDialog(QDialog):
    def __init__(self, database: Database, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Employees and work directory")
        self.resize(1050, 680)
        self.setMinimumSize(850, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        heading = QLabel("Employees & work directory")
        heading.setObjectName("PageTitle")
        layout.addWidget(heading)
        subtitle = QLabel(
            "Manage employees first, then customers, projects and their deployment sites."
        )
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        tabs = QTabWidget()
        for entity, title in (
            ("employee", "Employees"),
            ("customer", "Customers"),
            ("project", "Projects"),
            ("site", "Sites"),
        ):
            tabs.addTab(MasterTab(database, entity), title)
        layout.addWidget(tabs, 1)

        close_button = make_button("Done", role="Primary")
        close_button.clicked.connect(self.accept)
        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close_button)
        layout.addLayout(bottom)


class DeploymentDialog(QDialog):
    def __init__(
        self,
        database: Database,
        *,
        initial_date: QDate | None = None,
        deployment_id: int | None = None,
        copy_from_id: int | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        if deployment_id is not None and copy_from_id is not None:
            raise ValueError("Choose either edit or copy mode, not both.")
        self.database = database
        self.deployment_id = deployment_id
        self.is_copy = copy_from_id is not None
        source_id = deployment_id if deployment_id is not None else copy_from_id
        self.record = (
            database.get_deployment(source_id) if source_id is not None else None
        )
        if source_id is not None and self.record is None:
            raise ValueError("The selected deployment no longer exists.")
        dialog_title = (
            "Copy deployment"
            if self.is_copy
            else "Edit deployment"
            if self.record
            else "New deployment"
        )
        self.setWindowTitle(dialog_title)
        self.resize(650, 720)
        self.setMinimumSize(560, 560)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        title = QLabel(dialog_title if self.record else "Create deployment")
        title.setObjectName("PageTitle")
        outer.addWidget(title)
        if self.is_copy:
            subtitle_text = (
                "Choose the new deployment date. Work details are copied, while "
                "status starts as Scheduled and payment starts as pending."
            )
        elif self.record:
            subtitle_text = "Update this employee's deployment record."
        else:
            subtitle_text = (
                "Assign one or several employees to a customer project and site. "
                "A day rate applies separately to every selected employee."
            )
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        form = QFormLayout(body)
        form.setContentsMargins(4, 14, 12, 14)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(13)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        value_date = initial_date or QDate.currentDate()
        if self.record and self.is_copy and initial_date is None:
            value_date = QDate.fromString(
                self.record["work_date"], "yyyy-MM-dd"
            ).addDays(1)
        elif self.record and not self.is_copy:
            value_date = QDate.fromString(self.record["work_date"], "yyyy-MM-dd")
        self.work_date = make_date_edit(value_date)
        form.addRow("Deployment date *", self.work_date)

        if self.record:
            self.employee_combo = AdaptiveComboBox()
            for row in database.list_master("employee", active_only=False):
                suffix = "" if row["active"] else " (inactive)"
                self.employee_combo.addItem(row["name"] + suffix, row["id"])
            form.addRow("Employee *", self.employee_combo)
            self.employee_list = None
        else:
            self.employee_combo = None
            self.employee_list = QListWidget()
            self.employee_list.setMinimumHeight(140)
            self.employee_list.setSelectionMode(
                QAbstractItemView.SelectionMode.NoSelection
            )
            for row in database.list_master("employee", active_only=True):
                item = QListWidgetItem(row["name"])
                item.setData(Qt.ItemDataRole.UserRole, row["id"])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setToolTip(row.get("designation") or "")
                self.employee_list.addItem(item)
            form.addRow("Employees *", self.employee_list)

        self.customer = AdaptiveComboBox()
        self.customer.addItem("Select customer", None)
        for row in database.list_master(
            "customer", active_only=not bool(self.record)
        ):
            suffix = "" if row["active"] else " (inactive)"
            self.customer.addItem(row["name"] + suffix, row["id"])
        self.customer.currentIndexChanged.connect(self._refresh_related)
        form.addRow("Customer *", self.customer)

        self.project = AdaptiveComboBox()
        self.site = AdaptiveComboBox()
        form.addRow("Project *", self.project)
        form.addRow("Site *", self.site)

        time_row = QWidget()
        time_layout = QHBoxLayout(time_row)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(9)
        self.start_time = WheelSafeTimeEdit(QTime(9, 0))
        self.start_time.setDisplayFormat("hh:mm AP")
        self.end_time = WheelSafeTimeEdit(QTime(18, 0))
        self.end_time.setDisplayFormat("hh:mm AP")
        time_layout.addWidget(self.start_time)
        time_layout.addWidget(_plain_label("to", muted=True))
        time_layout.addWidget(self.end_time)
        form.addRow("Working time *", time_row)

        self.work_type = AdaptiveComboBox()
        self.work_type.addItems(
            ["Full day", "Half day – AM", "Half day – PM", "Overtime", "Travel", "Office"]
        )
        form.addRow("Work type", self.work_type)

        self.status = AdaptiveComboBox()
        self.status.addItems(["Scheduled", "Confirmed", "Completed", "Cancelled"])
        form.addRow("Status", self.status)

        self.day_basis = QCheckBox("This is day-basis work")
        self.day_basis.setToolTip(
            "Enable this when the employee is paid a fixed amount for this work date."
        )
        form.addRow("Payment basis", self.day_basis)

        self.payment_panel = QFrame()
        self.payment_panel.setObjectName("PaymentPanel")
        payment_layout = QHBoxLayout(self.payment_panel)
        payment_layout.setContentsMargins(12, 8, 12, 8)
        payment_layout.setSpacing(10)
        self.day_rate = WheelSafeDoubleSpinBox()
        self.day_rate.setDecimals(2)
        self.day_rate.setRange(0, 10_000_000)
        self.day_rate.setSingleStep(100)
        self.day_rate.setPrefix("₹ ")
        self.day_rate.setGroupSeparatorShown(True)
        self.day_rate.setMinimumWidth(180)
        payment_layout.addWidget(self.day_rate)
        per_day = _plain_label("per employee / day", muted=True)
        payment_layout.addWidget(per_day)
        payment_layout.addStretch()
        self.payment_completed = QCheckBox("Payment completed")
        payment_layout.addWidget(self.payment_completed)
        form.addRow("Day rate *", self.payment_panel)
        self.payment_label = form.labelForField(self.payment_panel)
        self.day_basis.toggled.connect(self._sync_payment_controls)

        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText(
            "Work scope, contact person, travel details or special instructions"
        )
        self.notes.setMaximumHeight(115)
        form.addRow("Notes", self.notes)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("Primary")
        if self.is_copy:
            self.buttons.button(QDialogButtonBox.StandardButton.Save).setText(
                "Create copy"
            )
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)
        outer.addWidget(self.buttons)

        self._refresh_related()
        if self.record:
            self._load_record()
        self._sync_payment_controls(self.day_basis.isChecked())

        if (
            (self.employee_list is not None and self.employee_list.count() == 0)
            or self.customer.count() <= 1
        ):
            self.buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(False)
            QMessageBox.information(
                self,
                "Directory setup required",
                "Add active employees, customers, projects and sites in the Directory first.",
            )

    def _refresh_related(self) -> None:
        customer_id = self.customer.currentData()
        current_project = self.project.currentData()
        current_site = self.site.currentData()
        self.project.blockSignals(True)
        self.site.blockSignals(True)
        self.project.clear()
        self.site.clear()
        self.project.addItem("Select project", None)
        self.site.addItem("Select site", None)
        if customer_id:
            for row in self.database.list_master(
                "project",
                active_only=not bool(self.record),
                customer_id=int(customer_id),
            ):
                code = f"{row['project_code']} — " if row.get("project_code") else ""
                suffix = "" if row["active"] else " (inactive)"
                self.project.addItem(code + row["name"] + suffix, row["id"])
            for row in self.database.list_master(
                "site",
                active_only=not bool(self.record),
                customer_id=int(customer_id),
            ):
                location = f" · {row['city']}" if row.get("city") else ""
                suffix = "" if row["active"] else " (inactive)"
                self.site.addItem(row["name"] + location + suffix, row["id"])
        set_combo_value(self.project, current_project)
        set_combo_value(self.site, current_site)
        self.project.blockSignals(False)
        self.site.blockSignals(False)

    def _load_record(self) -> None:
        assert self.record is not None and self.employee_combo is not None
        set_combo_value(self.employee_combo, self.record["employee_id"])
        set_combo_value(self.customer, self.record["customer_id"])
        self._refresh_related()
        set_combo_value(self.project, self.record["project_id"])
        set_combo_value(self.site, self.record["site_id"])
        self.start_time.setTime(QTime.fromString(self.record["start_time"], "HH:mm"))
        self.end_time.setTime(QTime.fromString(self.record["end_time"], "HH:mm"))
        index = self.work_type.findText(self.record["work_type"])
        if index >= 0:
            self.work_type.setCurrentIndex(index)
        index = self.status.findText(self.record["status"])
        if index >= 0:
            self.status.setCurrentIndex(index)
        self.day_rate.setValue(float(self.record.get("day_rate") or 0))
        self.payment_completed.setChecked(
            bool(self.record.get("payment_completed", 0))
        )
        self.day_basis.setChecked(bool(self.record.get("day_basis", 0)))
        self.notes.setPlainText(self.record.get("notes") or "")
        if self.is_copy:
            self.status.setCurrentText("Scheduled")
            self.payment_completed.setChecked(False)

    def _sync_payment_controls(self, enabled: bool) -> None:
        self.payment_panel.setVisible(enabled)
        if self.payment_label is not None:
            self.payment_label.setVisible(enabled)
        if not enabled:
            self.payment_completed.setChecked(False)

    def _employee_ids(self) -> list[int]:
        if self.employee_combo is not None:
            value = self.employee_combo.currentData()
            return [int(value)] if value else []
        assert self.employee_list is not None
        result: list[int] = []
        for index in range(self.employee_list.count()):
            item = self.employee_list.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                result.append(int(item.data(Qt.ItemDataRole.UserRole)))
        return result

    def _values(self) -> dict[str, Any]:
        return {
            "work_date": self.work_date.date().toString("yyyy-MM-dd"),
            "customer_id": self.customer.currentData(),
            "project_id": self.project.currentData(),
            "site_id": self.site.currentData(),
            "start_time": self.start_time.time().toString("HH:mm"),
            "end_time": self.end_time.time().toString("HH:mm"),
            "work_type": self.work_type.currentText(),
            "status": self.status.currentText(),
            "day_basis": self.day_basis.isChecked(),
            "day_rate": self.day_rate.value() if self.day_basis.isChecked() else 0,
            "payment_completed": (
                self.payment_completed.isChecked() if self.day_basis.isChecked() else False
            ),
            "notes": self.notes.toPlainText().strip(),
        }

    def _save(self) -> None:
        employee_ids = self._employee_ids()
        values = self._values()
        if not employee_ids:
            QMessageBox.warning(self, "Employee required", "Select at least one employee.")
            return
        if not all(values.get(key) for key in ("customer_id", "project_id", "site_id")):
            QMessageBox.warning(
                self,
                "Missing information",
                "Select a customer, project and site.",
            )
            return

        conflicts = self.database.find_conflicts(
            values["work_date"],
            employee_ids,
            exclude_id=self.deployment_id,
        )
        if conflicts:
            lines = [
                f"• {row['employee_name']}: {row['project_name']} at {row['site_name']}"
                for row in conflicts[:8]
            ]
            if len(conflicts) > 8:
                lines.append(f"• …and {len(conflicts) - 8} more")
            answer = QMessageBox.warning(
                self,
                "Existing deployment found",
                "The following employees already have a deployment on this date:\n\n"
                + "\n".join(lines)
                + "\n\nSave anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        try:
            if self.deployment_id is None:
                self.database.add_deployments(values, employee_ids)
            else:
                values["employee_id"] = employee_ids[0]
                self.database.update_deployment(self.deployment_id, values)
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot save deployment", str(exc))
            return
        self.accept()


class DayEntriesDialog(QDialog):
    def __init__(
        self,
        database: Database,
        day: QDate,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.database = database
        self.day = day
        self.changed = False
        self.setWindowTitle(day.toString("dddd, dd MMMM yyyy"))
        self.resize(720, 560)
        self.setMinimumSize(600, 430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel(day.toString("dddd, dd MMMM yyyy"))
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        self.count_label = QLabel()
        self.count_label.setObjectName("Muted")
        layout.addWidget(self.count_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.cards = QVBoxLayout(self.container)
        self.cards.setContentsMargins(2, 8, 8, 8)
        self.cards.setSpacing(9)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        controls = QHBoxLayout()
        add = make_button("Add deployment", role="Primary")
        close = make_button("Close")
        add.clicked.connect(self._add)
        close.clicked.connect(self.accept)
        controls.addWidget(add)
        controls.addStretch()
        controls.addWidget(close)
        layout.addLayout(controls)
        self._rebuild()

    def _rows(self) -> list[dict[str, Any]]:
        return self.database.list_deployments(
            date_from=self.day.toString("yyyy-MM-dd"),
            date_to=self.day.toString("yyyy-MM-dd"),
        )

    def _clear_cards(self) -> None:
        while self.cards.count():
            item = self.cards.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _rebuild(self) -> None:
        self._clear_cards()
        rows = self._rows()
        self.count_label.setText(
            f"{len(rows)} deployment{'s' if len(rows) != 1 else ''}"
        )
        if not rows:
            empty = QLabel("No deployments on this date.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("Muted")
            empty.setMinimumHeight(170)
            self.cards.addWidget(empty)
        for row in rows:
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(13, 11, 11, 11)

            color = QFrame()
            color.setFixedWidth(5)
            color.setStyleSheet(
                f"background: {row.get('employee_color') or COLORS['primary']}; "
                "border-radius: 2px;"
            )
            card_layout.addWidget(color)

            details = QVBoxLayout()
            heading = QLabel(
                f"{row['employee_name']}  ·  {row['project_name']}"
            )
            heading.setObjectName("SectionTitle")
            heading.setTextFormat(Qt.TextFormat.PlainText)
            details.addWidget(heading)
            meta = QLabel(
                f"{row['customer_name']}  •  {row['site_name']}"
                + (f", {row['site_city']}" if row.get("site_city") else "")
            )
            meta.setObjectName("Muted")
            meta.setTextFormat(Qt.TextFormat.PlainText)
            details.addWidget(meta)
            timing = QLabel(
                f"{row['start_time']}–{row['end_time']}  •  "
                f"{row['work_type']}  •  {row['status']}"
            )
            timing.setObjectName("Muted")
            details.addWidget(timing)
            if row.get("day_basis"):
                completed = bool(row.get("payment_completed"))
                payment = QLabel(
                    f"Day basis  •  {format_currency(row.get('day_rate'))} per day  •  "
                    + ("Payment completed" if completed else "Payment pending")
                )
                payment.setStyleSheet(
                    "color: #14947E; font-weight: 700;"
                    if completed
                    else "color: #B7791F; font-weight: 700;"
                )
                details.addWidget(payment)
            if row.get("notes"):
                note = QLabel(row["notes"])
                note.setWordWrap(True)
                note.setTextFormat(Qt.TextFormat.PlainText)
                details.addWidget(note)
            card_layout.addLayout(details, 1)

            copy = make_button("Copy")
            edit = make_button("Edit")
            delete = make_button("Delete", role="Danger")
            copy.clicked.connect(
                lambda _checked=False, item_id=row["id"]: self._copy(item_id)
            )
            edit.clicked.connect(
                lambda _checked=False, item_id=row["id"]: self._edit(item_id)
            )
            delete.clicked.connect(
                lambda _checked=False, item_id=row["id"]: self._delete(item_id)
            )
            card_layout.addWidget(copy)
            card_layout.addWidget(edit)
            card_layout.addWidget(delete)
            self.cards.addWidget(card)
        self.cards.addStretch()

    def _add(self) -> None:
        if DeploymentDialog(
            self.database, initial_date=self.day, parent=self
        ).exec():
            self.changed = True
            self._rebuild()

    def _edit(self, deployment_id: int) -> None:
        if DeploymentDialog(
            self.database, deployment_id=deployment_id, parent=self
        ).exec():
            self.changed = True
            self._rebuild()

    def _copy(self, deployment_id: int) -> None:
        if DeploymentDialog(
            self.database, copy_from_id=deployment_id, parent=self
        ).exec():
            self.changed = True
            self._rebuild()

    def _delete(self, deployment_id: int) -> None:
        answer = QMessageBox.question(
            self,
            "Delete deployment",
            "Delete this deployment permanently?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.delete_deployment(deployment_id)
            self.changed = True
            self._rebuild()
