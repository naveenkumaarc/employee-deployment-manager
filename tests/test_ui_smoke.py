from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from deployment_manager.database import Database
from deployment_manager.dialogs import DeploymentDialog
from deployment_manager.icons import write_icon_assets
from deployment_manager.main_window import MainWindow


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
            "customer_id": customer,
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
    assert ico_path.exists()
    assert ico_path.stat().st_size > 1000
    app.processEvents()


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
        dialog.close()

        window = MainWindow(database, tmp_path)
        window.show()
        app.processEvents()
        preview = window.grab()
        assert not preview.isNull()
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
