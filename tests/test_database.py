from __future__ import annotations

from datetime import date

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
