from __future__ import annotations

from datetime import date
import sqlite3

import pytest

from deployment_manager.database import Database


@pytest.fixture
def database(tmp_path):
    instance = Database(tmp_path / "deployment_desk.db")
    yield instance
    instance.close()


def seed_directory(database: Database) -> dict[str, int]:
    employee_one = database.save_master(
        "employee",
        {
            "employee_code": "EMP-001",
            "name": "Asha Rao",
            "designation": "Site Engineer",
            "phone": "555-0101",
            "email": "asha@example.com",
            "color": "#526DFE",
            "active": True,
        },
    )
    employee_two = database.save_master(
        "employee",
        {
            "employee_code": "EMP-002",
            "name": "Daniel Lee",
            "designation": "Technician",
            "phone": "555-0102",
            "email": "daniel@example.com",
            "color": "#19B8A4",
            "active": True,
        },
    )
    customer = database.save_master(
        "customer",
        {
            "name": "Northwind Industries",
            "contact_person": "Maya Patel",
            "phone": "555-0110",
            "email": "maya@northwind.example",
            "address": "12 Industrial Road",
            "active": True,
        },
    )
    project = database.save_master(
        "project",
        {
            "customer_id": customer,
            "project_code": "NW-24",
            "name": "Plant Upgrade",
            "description": "Electrical and controls upgrade",
            "active": True,
        },
    )
    site = database.save_master(
        "site",
        {
            "customer_id": customer,
            "name": "North Plant",
            "city": "Pune",
            "address": "North industrial estate",
            "active": True,
        },
    )
    return {
        "employee_one": employee_one,
        "employee_two": employee_two,
        "customer": customer,
        "project": project,
        "site": site,
    }


def deployment_values(ids: dict[str, int], work_date: str) -> dict[str, object]:
    return {
        "work_date": work_date,
        "customer_id": ids["customer"],
        "project_id": ids["project"],
        "site_id": ids["site"],
        "start_time": "09:00",
        "end_time": "18:00",
        "work_type": "Full day",
        "status": "Scheduled",
        "notes": "Commissioning support",
    }


def test_directory_crud_and_active_filter(database: Database):
    assert database.required_data_ready() is False
    ids = seed_directory(database)
    assert database.required_data_ready() is True

    employees = database.list_master("employee", active_only=True)
    assert [row["name"] for row in employees] == ["Asha Rao", "Daniel Lee"]

    database.set_master_active("employee", ids["employee_two"], False)
    active_names = [
        row["name"] for row in database.list_master("employee", active_only=True)
    ]
    assert active_names == ["Asha Rao"]

    updated = database.get_master("employee", ids["employee_one"])
    assert updated is not None
    updated["designation"] = "Senior Site Engineer"
    database.save_master("employee", updated, ids["employee_one"])
    assert (
        database.get_master("employee", ids["employee_one"])["designation"]
        == "Senior Site Engineer"
    )


def test_bulk_deployment_filters_conflicts_and_counts(database: Database):
    ids = seed_directory(database)
    work_date = date.today().isoformat()
    created = database.add_deployments(
        deployment_values(ids, work_date),
        [ids["employee_one"], ids["employee_two"], ids["employee_one"]],
    )
    assert len(created) == 2

    rows = database.list_deployments(
        date_from=work_date,
        date_to=work_date,
        customer_id=ids["customer"],
        search="Plant Upgrade",
    )
    assert len(rows) == 2
    assert {row["employee_name"] for row in rows} == {"Asha Rao", "Daniel Lee"}

    events = database.month_events(date.today().year, date.today().month)
    assert len(events[work_date]) == 2

    conflicts = database.find_conflicts(
        work_date, [ids["employee_one"], ids["employee_two"]]
    )
    assert {row["employee_name"] for row in conflicts} == {"Asha Rao", "Daniel Lee"}

    counts = database.dashboard_counts(date.today().year, date.today().month)
    assert counts["today"] == 2
    assert counts["month"] == 2
    assert counts["employees"] == 2
    assert counts["customers"] == 1

    update = deployment_values(ids, work_date)
    update.update(
        {
            "employee_id": ids["employee_one"],
            "status": "Completed",
            "notes": "Completed safely",
        }
    )
    database.update_deployment(created[0], update)
    assert database.get_deployment(created[0])["status"] == "Completed"

    database.delete_deployment(created[1])
    assert len(database.list_deployments()) == 1


def test_validation_and_backup(database: Database, tmp_path):
    ids = seed_directory(database)
    other_customer = database.save_master(
        "customer", {"name": "Contoso", "active": True}
    )
    other_site = database.save_master(
        "site",
        {
            "customer_id": other_customer,
            "name": "Contoso Yard",
            "active": True,
        },
    )

    invalid = deployment_values(ids, "2026-01-15")
    invalid["site_id"] = other_site
    with pytest.raises(ValueError, match="site does not belong"):
        database.add_deployments(invalid, [ids["employee_one"]])

    invalid_time = deployment_values(ids, "2026-01-15")
    invalid_time["start_time"] = "18:00"
    invalid_time["end_time"] = "09:00"
    with pytest.raises(ValueError, match="End time"):
        database.add_deployments(invalid_time, [ids["employee_one"]])

    invalid_rate = deployment_values(ids, "2026-01-15")
    invalid_rate.update({"day_basis": True, "day_rate": 0})
    with pytest.raises(ValueError, match="greater than zero"):
        database.add_deployments(invalid_rate, [ids["employee_one"]])

    database.add_deployments(
        deployment_values(ids, "2026-01-15"), [ids["employee_one"]]
    )
    backup_path = database.backup_to(tmp_path / "backups" / "copy.db")
    assert backup_path.exists()

    backup = Database(backup_path)
    try:
        assert len(backup.list_deployments()) == 1
        assert backup.list_deployments()[0]["project_name"] == "Plant Upgrade"
    finally:
        backup.close()


def test_day_basis_payment_fields_and_filters(database: Database):
    ids = seed_directory(database)

    pending = deployment_values(ids, "2026-08-31")
    pending.update(
        {"day_basis": True, "day_rate": 1750.0, "payment_completed": False}
    )
    pending_id = database.add_deployments(pending, [ids["employee_one"]])[0]

    completed = deployment_values(ids, "2026-09-01")
    completed.update(
        {"day_basis": True, "day_rate": 2200.0, "payment_completed": True}
    )
    database.add_deployments(completed, [ids["employee_two"]])

    ordinary = deployment_values(ids, "2026-09-02")
    database.add_deployments(ordinary, [ids["employee_one"]])

    day_basis_rows = database.list_deployments(day_basis=True)
    assert len(day_basis_rows) == 2
    assert sum(row["day_rate"] for row in day_basis_rows) == 3950.0

    pending_rows = database.list_deployments(
        day_basis=True, payment_completed=False
    )
    assert [row["id"] for row in pending_rows] == [pending_id]
    assert len(
        database.list_deployments(day_basis=True, payment_completed=True)
    ) == 1

    update = database.get_deployment(pending_id)
    assert update is not None
    update["payment_completed"] = True
    database.update_deployment(pending_id, update)
    assert database.get_deployment(pending_id)["payment_completed"] == 1


def test_calendar_grid_includes_adjacent_month_entries(database: Database):
    ids = seed_directory(database)
    database.add_deployments(
        deployment_values(ids, "2026-08-31"), [ids["employee_one"]]
    )

    september_grid = database.month_events(2026, 9)
    assert "2026-08-31" in september_grid
    assert september_grid["2026-08-31"][0]["employee_name"] == "Asha Rao"


def test_existing_version_one_database_migrates_without_data_loss(tmp_path):
    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date TEXT NOT NULL,
            employee_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            site_id INTEGER NOT NULL,
            start_time TEXT NOT NULL DEFAULT '09:00',
            end_time TEXT NOT NULL DEFAULT '18:00',
            work_type TEXT NOT NULL DEFAULT 'Full day',
            status TEXT NOT NULL DEFAULT 'Scheduled',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO deployments (
            work_date, employee_id, customer_id, project_id, site_id,
            start_time, end_time, work_type, status, notes, created_at, updated_at
        ) VALUES (
            '2026-08-31', 1, 1, 1, 1, '09:00', '18:00', 'Full day',
            'Scheduled', 'Legacy record preserved', '2026-08-01', '2026-08-01'
        );
        PRAGMA user_version = 1;
        """
    )
    connection.close()

    migrated = Database(path)
    try:
        columns = {
            row["name"]
            for row in migrated.connection.execute("PRAGMA table_info(deployments)")
        }
        assert {"day_basis", "day_rate", "payment_completed"}.issubset(columns)
        assert migrated.connection.execute("PRAGMA user_version").fetchone()[0] == 2
        row = migrated.connection.execute(
            "SELECT notes, day_basis, day_rate, payment_completed FROM deployments"
        ).fetchone()
        assert tuple(row) == ("Legacy record preserved", 0, 0.0, 0)
    finally:
        migrated.close()
