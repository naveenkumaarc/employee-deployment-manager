from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QDate, QEvent
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox

from deployment_manager.database import Database
from deployment_manager.dialogs import DayEntriesDialog, DeploymentDialog
from deployment_manager.icons import write_icon_assets
from deployment_manager.main_window import MainWindow
from deployment_manager.theme import APP_STYLE


def seed(database: Database) -> None:
    employee = database.save_master(
        "employee",
        {
            "employee_code": "EMP-01",
            "name": "Test Employee",
            "designation": "Engineer",
            "color": "#526DFE",
            "active": True,
        },
    )
    customer = database.save_master(
        "customer", {"name": "Test Customer", "active": True}
    )
    project = database.save_master(
        "project",
        {
            "customer_id": customer,
            "project_code": "P-01",
            "name": "Test Project",
            "active": True,
        },
    )
    site = database.save_master(
        "site",
        {
            "name": "Test Site",
            "city": "Chennai",
            "active": True,
        },
    )
    database.add_deployments(
        {
            "work_date": QDate.currentDate().toString("yyyy-MM-dd"),
            "customer_id": customer,
            "project_id": project,
            "site_id": site,
            "start_time": "09:00",
            "end_time": "18:00",
            "work_type": "Full day",
            "status": "Confirmed",
            "day_basis": True,
            "day_rate": 1850,
            "payment_completed": False,
            "notes": "UI smoke test",
        },
        [employee],
    )


def test_icon_assets_have_transparent_rounded_corners(tmp_path):
    app = QApplication.instance() or QApplication([])
    png_path, ico_path = write_icon_assets(tmp_path / "assets", overwrite=True)

    image = QImage(str(png_path))
    assert not image.isNull()
    assert image.width() == 512
    assert image.pixelColor(0, 0).alpha() == 0
    assert image.pixelColor(256, 256).alpha() == 255
    green_pixel = image.pixelColor(256, 64)
    assert green_pixel.green() > green_pixel.red()
    assert ico_path.exists()
    assert ico_path.stat().st_size > 1000
    app.processEvents()


def test_theme_tokens_render_without_partial_placeholder_suffixes():
    assert "@color_" not in APP_STYLE
    assert "@font_" not in APP_STYLE
    assert "_soft" not in APP_STYLE
    assert "_hover" not in APP_STYLE
    assert "_pressed" not in APP_STYLE
    assert "_strong" not in APP_STYLE
    assert "_alt" not in APP_STYLE


def test_main_window_and_deployment_dialog_render_offscreen(tmp_path):
    app = QApplication.instance() or QApplication([])
    database = Database(tmp_path / "ui.db")
    try:
        seed(database)
        dialog = DeploymentDialog(database, initial_date=QDate.currentDate())
        assert dialog.employee_list is not None
        assert dialog.employee_list.count() == 1
        dialog.day_basis.setChecked(True)
        assert not dialog.payment_panel.isHidden()
        dialog.day_rate.setValue(1500)
        assert dialog._values()["day_rate"] == 1500
        assert "payment_completed" not in dialog._values()
        assert dialog.start_time.text() == "09:00 AM"
        assert dialog.end_time.text() == "06:00 PM"
        assert dialog.day_rate.text().strip() == "₹ 1,500.00"
        dialog.close()

        window = MainWindow(database, tmp_path)
        window.show()
        app.processEvents()
        preview = window.grab()
        assert not preview.isNull()
        assert window.windowTitle() == "Deployment Desk"
        calendar_grid = window.calendar_page.calendar._calendar_grid
        assert calendar_grid is not None
        last_row = calendar_grid.model().rowCount() - 1
        last_cell = calendar_grid.visualRect(calendar_grid.model().index(last_row, 0))
        assert last_cell.bottom() <= calendar_grid.viewport().rect().bottom()
        assert window.calendar_page.calendar.events_for(QDate.currentDate())
        assert window.reports_page.summary_rows[0]["total_amount"] == 1850
        assert window.reports_page.summary_rows[0]["pending_amount"] == 1850

        window.calendar_page.calendar.setCurrentPage(2026, 9)
        window.calendar_page.refresh()
        database.add_deployments(
            {
                "work_date": "2026-08-31",
                "customer_id": database.list_master("customer")[0]["id"],
                "project_id": database.list_master("project")[0]["id"],
                "site_id": database.list_master("site")[0]["id"],
                "start_time": "09:00",
                "end_time": "18:00",
                "work_type": "Full day",
                "status": "Scheduled",
                "notes": "Month boundary test",
            },
            [database.list_master("employee")[0]["id"]],
        )
        window.calendar_page.refresh()
        assert window.calendar_page.calendar.events_for(QDate(2026, 8, 31))
        window.close()
        app.processEvents()
    finally:
        database.close()


def test_copy_dialog_uses_next_date_and_resets_completion(tmp_path):
    app = QApplication.instance() or QApplication([])
    database = Database(tmp_path / "copy.db")
    try:
        seed(database)
        source = database.list_deployments()[0]
        source["status"] = "Completed"
        database.update_deployment(source["id"], source)
        database.set_payment_completed(source["id"], True)

        dialog = DeploymentDialog(database, copy_from_id=source["id"])
        values = dialog._values()
        assert dialog.is_copy is True
        assert dialog.deployment_id is None
        assert dialog.employee_combo is not None
        assert dialog.employee_combo.currentData() == source["employee_id"]
        assert values["work_date"] == QDate.currentDate().addDays(1).toString(
            "yyyy-MM-dd"
        )
        assert values["status"] == "Scheduled"
        assert "payment_completed" not in values

        created = database.add_deployments(values, dialog._employee_ids())
        assert len(created) == 1
        assert len(database.list_deployments()) == 2
        dialog.close()
        app.processEvents()
    finally:
        database.close()


def test_deployment_date_navigation_preserves_form_state_and_rolls_over(tmp_path):
    app = QApplication.instance() or QApplication([])
    database = Database(tmp_path / "date_navigation.db")
    try:
        seed(database)
        dialog = DeploymentDialog(database, initial_date=QDate(2026, 12, 31))
        dialog.notes.setPlainText("Keep this work scope")
        dialog.day_basis.setChecked(True)
        dialog.day_rate.setValue(2750)

        dialog.next_date_button.click()
        assert dialog.work_date.date() == QDate(2027, 1, 1)
        assert dialog.notes.toPlainText() == "Keep this work scope"
        assert dialog.day_rate.value() == 2750

        dialog.work_date.setDate(QDate(2028, 3, 1))
        dialog.previous_date_button.click()
        assert dialog.work_date.date() == QDate(2028, 2, 29)
        assert dialog.work_date.displayFormat() == "dd MMM yyyy"
        dialog.close()
        app.processEvents()
    finally:
        database.close()


def test_deployment_site_picker_lists_all_sites_independent_of_customer(tmp_path):
    app = QApplication.instance() or QApplication([])
    database = Database(tmp_path / "site_picker.db")
    try:
        seed(database)
        second_customer = database.save_master(
            "customer", {"name": "Another Customer", "active": True}
        )
        second_site = database.save_master(
            "site", {"name": "Independent Site", "city": "Pune", "active": True}
        )
        dialog = DeploymentDialog(database, initial_date=QDate.currentDate())

        site_ids = {
            dialog.site.itemData(index) for index in range(1, dialog.site.count())
        }
        assert second_site in site_ids
        assert "customer_id" not in database.get_master("site", second_site)

        dialog.site.setCurrentIndex(dialog.site.findData(second_site))
        dialog.customer.setCurrentIndex(dialog.customer.findData(second_customer))
        assert dialog.site.currentData() == second_site
        assert {
            dialog.site.itemData(index) for index in range(1, dialog.site.count())
        } == site_ids
        dialog.close()
        app.processEvents()
    finally:
        database.close()


def test_per_date_payment_action_is_conditional_and_reversible(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    database = Database(tmp_path / "payment_actions.db")
    try:
        seed(database)
        day = QDate.currentDate()
        day_basis = database.list_deployments()[0]
        ordinary_values = {
            "work_date": day.toString("yyyy-MM-dd"),
            "customer_id": day_basis["customer_id"],
            "project_id": day_basis["project_id"],
            "site_id": day_basis["site_id"],
            "start_time": "10:00",
            "end_time": "17:00",
            "work_type": "Full day",
            "status": "Scheduled",
            "day_basis": False,
            "notes": "No payment action",
        }
        ordinary_id = database.add_deployments(
            ordinary_values, [day_basis["employee_id"]]
        )[0]

        dialog = DayEntriesDialog(database, day)
        assert set(dialog.payment_buttons) == {day_basis["id"]}
        assert ordinary_id not in dialog.payment_buttons
        assert dialog.payment_buttons[day_basis["id"]].text() == "Mark Payment Complete"

        dialog.payment_buttons[day_basis["id"]].click()
        app.processEvents()
        assert database.get_deployment(day_basis["id"])["payment_completed"] == 1
        assert dialog.payment_buttons[day_basis["id"]].text() == "Undo Payment"
        assert any(
            label.objectName() == "PaidBadge" and label.text() == "Paid"
            for label in dialog.findChildren(QLabel)
        )

        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )
        dialog.payment_buttons[day_basis["id"]].click()
        app.processEvents()
        assert database.get_deployment(day_basis["id"])["payment_completed"] == 0
        assert dialog.payment_buttons[day_basis["id"]].text() == "Mark Payment Complete"
        dialog.close()
        app.processEvents()
    finally:
        database.close()


def test_per_date_window_navigates_days_without_closing(tmp_path):
    app = QApplication.instance() or QApplication([])
    database = Database(tmp_path / "day_entries_navigation.db")
    try:
        seed(database)
        source = database.list_deployments()[0]
        values = {
            "work_date": "2026-12-31",
            "customer_id": source["customer_id"],
            "project_id": source["project_id"],
            "site_id": source["site_id"],
            "start_time": "09:00",
            "end_time": "18:00",
            "work_type": "Full day",
            "status": "Scheduled",
            "day_basis": False,
            "notes": "Year-end deployment",
        }
        database.add_deployments(values, [source["employee_id"]])
        values["work_date"] = "2027-01-01"
        values["notes"] = "New-year deployment"
        database.add_deployments(values, [source["employee_id"]])

        dialog = DayEntriesDialog(database, QDate(2026, 12, 31))
        dialog.show()
        app.processEvents()
        assert dialog.isVisible()
        assert dialog.count_label.text() == "1 deployment"

        dialog.next_day_button.click()
        app.processEvents()
        assert dialog.isVisible()
        assert dialog.day == QDate(2027, 1, 1)
        assert dialog.windowTitle() == "Friday, 01 January 2027"
        assert dialog.title_label.text() == "Friday, 01 January 2027"
        assert dialog.count_label.text() == "1 deployment"

        dialog.next_day_button.click()
        assert dialog.day == QDate(2027, 1, 2)
        assert dialog.count_label.text() == "0 deployments"

        dialog.previous_day_button.click()
        assert dialog.day == QDate(2027, 1, 1)
        assert dialog.count_label.text() == "1 deployment"
        dialog.close()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
    finally:
        database.close()
