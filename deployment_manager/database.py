from __future__ import annotations

import shutil
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

ENTITY_TABLES = {
    "employee": "employees",
    "customer": "customers",
    "project": "projects",
    "site": "sites",
}

ENTITY_FIELDS = {
    "employee": ("employee_code", "name", "designation", "phone", "email", "color", "active"),
    "customer": ("name", "contact_person", "phone", "email", "address", "active"),
    "project": ("customer_id", "project_code", "name", "description", "active"),
    "site": ("customer_id", "name", "city", "address", "active"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Database:
    """Small SQLite repository with explicit, testable operations."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path), timeout=15)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
        self.connection.execute("PRAGMA busy_timeout = 15000")
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT COLLATE NOCASE UNIQUE,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                designation TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                color TEXT NOT NULL DEFAULT '#D86F78',
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                contact_person TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                project_code TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL COLLATE NOCASE,
                description TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
                UNIQUE(customer_id, name)
            );

            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                name TEXT NOT NULL COLLATE NOCASE,
                city TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
                UNIQUE(customer_id, name)
            );

            CREATE TABLE IF NOT EXISTS deployments (
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
                day_basis INTEGER NOT NULL DEFAULT 0 CHECK(day_basis IN (0, 1)),
                day_rate REAL NOT NULL DEFAULT 0 CHECK(day_rate >= 0),
                payment_completed INTEGER NOT NULL DEFAULT 0
                    CHECK(payment_completed IN (0, 1)),
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE RESTRICT,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE RESTRICT,
                FOREIGN KEY(site_id) REFERENCES sites(id) ON DELETE RESTRICT,
                CHECK(length(work_date) = 10)
            );

            CREATE INDEX IF NOT EXISTS idx_deployments_date
                ON deployments(work_date);
            CREATE INDEX IF NOT EXISTS idx_deployments_employee_date
                ON deployments(employee_id, work_date);
            CREATE INDEX IF NOT EXISTS idx_deployments_customer_date
                ON deployments(customer_id, work_date);
            CREATE INDEX IF NOT EXISTS idx_deployments_project_date
                ON deployments(project_id, work_date);
            CREATE UNIQUE INDEX IF NOT EXISTS uq_deployment_exact
                ON deployments(work_date, employee_id, project_id, site_id, start_time);

            PRAGMA user_version = 2;
            """
        )
        self._migrate_schema()
        self.connection.commit()

    def _migrate_schema(self) -> None:
        """Add payment fields to databases created by Deployment Desk 1.0."""
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(deployments)")
        }
        migrations = {
            "day_basis": (
                "ALTER TABLE deployments ADD COLUMN day_basis INTEGER NOT NULL "
                "DEFAULT 0 CHECK(day_basis IN (0, 1))"
            ),
            "day_rate": (
                "ALTER TABLE deployments ADD COLUMN day_rate REAL NOT NULL "
                "DEFAULT 0 CHECK(day_rate >= 0)"
            ),
            "payment_completed": (
                "ALTER TABLE deployments ADD COLUMN payment_completed INTEGER NOT NULL "
                "DEFAULT 0 CHECK(payment_completed IN (0, 1))"
            ),
        }
        for column, statement in migrations.items():
            if column not in columns:
                self.connection.execute(statement)
        self.connection.execute("PRAGMA user_version = 2")

    @staticmethod
    def _dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.connection.close()

    def required_data_ready(self) -> bool:
        row = self.connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM employees WHERE active = 1) AS employees,
                (SELECT COUNT(*) FROM customers WHERE active = 1) AS customers,
                (SELECT COUNT(*) FROM projects WHERE active = 1) AS projects,
                (SELECT COUNT(*) FROM sites WHERE active = 1) AS sites
            """
        ).fetchone()
        return bool(row and all(row[key] > 0 for key in row.keys()))

    def list_master(
        self,
        entity: str,
        *,
        active_only: bool = False,
        customer_id: int | None = None,
    ) -> list[dict[str, Any]]:
        if entity not in ENTITY_TABLES:
            raise ValueError(f"Unsupported entity: {entity}")

        where: list[str] = []
        params: list[Any] = []
        if active_only:
            where.append("t.active = 1")
        if customer_id is not None and entity in {"project", "site"}:
            where.append("t.customer_id = ?")
            params.append(customer_id)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        if entity in {"project", "site"}:
            sql = f"""
                SELECT t.*, c.name AS customer_name
                FROM {ENTITY_TABLES[entity]} t
                JOIN customers c ON c.id = t.customer_id
                {where_sql}
                ORDER BY c.name COLLATE NOCASE, t.name COLLATE NOCASE
            """
        else:
            sql = f"""
                SELECT t.*
                FROM {ENTITY_TABLES[entity]} t
                {where_sql}
                ORDER BY t.name COLLATE NOCASE
            """
        return self._dicts(self.connection.execute(sql, params).fetchall())

    def get_master(self, entity: str, record_id: int) -> dict[str, Any] | None:
        if entity not in ENTITY_TABLES:
            raise ValueError(f"Unsupported entity: {entity}")
        row = self.connection.execute(
            f"SELECT * FROM {ENTITY_TABLES[entity]} WHERE id = ?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def save_master(
        self,
        entity: str,
        values: dict[str, Any],
        record_id: int | None = None,
    ) -> int:
        if entity not in ENTITY_TABLES:
            raise ValueError(f"Unsupported entity: {entity}")

        fields = ENTITY_FIELDS[entity]
        payload = {field: values.get(field, "") for field in fields}
        payload["active"] = int(bool(payload.get("active", True)))
        if entity == "employee":
            payload["employee_code"] = str(payload["employee_code"]).strip() or None
            payload["color"] = str(payload["color"]).strip() or "#D86F78"

        for required in ("name",):
            if not str(payload.get(required, "")).strip():
                raise ValueError("Name is required.")
            payload[required] = str(payload[required]).strip()

        if entity in {"project", "site"} and not payload.get("customer_id"):
            raise ValueError("Customer is required.")

        now = utc_now()
        table = ENTITY_TABLES[entity]
        if record_id is None:
            insert_fields = (*fields, "created_at", "updated_at")
            placeholders = ", ".join("?" for _ in insert_fields)
            cursor = self.connection.execute(
                f"INSERT INTO {table} ({', '.join(insert_fields)}) VALUES ({placeholders})",
                [payload[field] for field in fields] + [now, now],
            )
            self.connection.commit()
            return int(cursor.lastrowid)

        assignments = ", ".join(f"{field} = ?" for field in fields)
        cursor = self.connection.execute(
            f"UPDATE {table} SET {assignments}, updated_at = ? WHERE id = ?",
            [payload[field] for field in fields] + [now, record_id],
        )
        if cursor.rowcount != 1:
            self.connection.rollback()
            raise ValueError("The selected record no longer exists.")
        self.connection.commit()
        return record_id

    def set_master_active(self, entity: str, record_id: int, active: bool) -> None:
        if entity not in ENTITY_TABLES:
            raise ValueError(f"Unsupported entity: {entity}")
        self.connection.execute(
            f"UPDATE {ENTITY_TABLES[entity]} SET active = ?, updated_at = ? WHERE id = ?",
            (int(active), utc_now(), record_id),
        )
        self.connection.commit()

    def _validate_relationships(
        self, customer_id: int, project_id: int, site_id: int
    ) -> None:
        project = self.connection.execute(
            "SELECT customer_id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        site = self.connection.execute(
            "SELECT customer_id FROM sites WHERE id = ?", (site_id,)
        ).fetchone()
        if not project or not site:
            raise ValueError("The selected project or site no longer exists.")
        if project["customer_id"] != customer_id:
            raise ValueError("The selected project does not belong to this customer.")
        if site["customer_id"] != customer_id:
            raise ValueError("The selected site does not belong to this customer.")

    @staticmethod
    def _validate_deployment(values: dict[str, Any]) -> None:
        try:
            date.fromisoformat(str(values["work_date"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("A valid deployment date is required.") from exc

        required_ids = ("customer_id", "project_id", "site_id")
        if any(not values.get(key) for key in required_ids):
            raise ValueError("Customer, project and site are required.")

        start = str(values.get("start_time", "09:00"))
        end = str(values.get("end_time", "18:00"))
        if len(start) != 5 or len(end) != 5 or start >= end:
            raise ValueError("End time must be later than start time.")

        if values.get("day_basis"):
            try:
                day_rate = float(values.get("day_rate", 0))
            except (TypeError, ValueError) as exc:
                raise ValueError("Enter a valid amount per employee per day.") from exc
            if day_rate <= 0:
                raise ValueError(
                    "Amount per employee per day must be greater than zero."
                )

    def find_conflicts(
        self,
        work_date: str,
        employee_ids: Iterable[int],
        *,
        exclude_id: int | None = None,
    ) -> list[dict[str, Any]]:
        ids = [int(item) for item in employee_ids]
        if not ids:
            return []
        marks = ", ".join("?" for _ in ids)
        params: list[Any] = [work_date, *ids]
        exclude_sql = ""
        if exclude_id is not None:
            exclude_sql = "AND d.id <> ?"
            params.append(exclude_id)
        rows = self.connection.execute(
            f"""
            SELECT d.id, d.employee_id, e.name AS employee_name,
                   c.name AS customer_name, p.name AS project_name,
                   s.name AS site_name, d.start_time, d.end_time
            FROM deployments d
            JOIN employees e ON e.id = d.employee_id
            JOIN customers c ON c.id = d.customer_id
            JOIN projects p ON p.id = d.project_id
            JOIN sites s ON s.id = d.site_id
            WHERE d.work_date = ?
              AND d.employee_id IN ({marks})
              AND d.status <> 'Cancelled'
              {exclude_sql}
            ORDER BY e.name
            """,
            params,
        ).fetchall()
        return self._dicts(rows)

    def add_deployments(
        self, values: dict[str, Any], employee_ids: Iterable[int]
    ) -> list[int]:
        self._validate_deployment(values)
        ids = list(dict.fromkeys(int(item) for item in employee_ids))
        if not ids:
            raise ValueError("Select at least one employee.")
        self._validate_relationships(
            int(values["customer_id"]), int(values["project_id"]), int(values["site_id"])
        )
        day_basis = int(bool(values.get("day_basis", False)))
        day_rate = float(values.get("day_rate", 0) or 0) if day_basis else 0.0
        payment_completed = (
            int(bool(values.get("payment_completed", False))) if day_basis else 0
        )
        now = utc_now()
        created: list[int] = []
        try:
            with self.connection:
                for employee_id in ids:
                    cursor = self.connection.execute(
                        """
                        INSERT INTO deployments (
                            work_date, employee_id, customer_id, project_id, site_id,
                            start_time, end_time, work_type, status,
                            day_basis, day_rate, payment_completed, notes,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            values["work_date"],
                            employee_id,
                            values["customer_id"],
                            values["project_id"],
                            values["site_id"],
                            values.get("start_time", "09:00"),
                            values.get("end_time", "18:00"),
                            values.get("work_type", "Full day"),
                            values.get("status", "Scheduled"),
                            day_basis,
                            day_rate,
                            payment_completed,
                            values.get("notes", "").strip(),
                            now,
                            now,
                        ),
                    )
                    created.append(int(cursor.lastrowid))
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "An identical deployment already exists for one of the selected employees."
            ) from exc
        return created

    def update_deployment(self, deployment_id: int, values: dict[str, Any]) -> None:
        self._validate_deployment(values)
        employee_id = int(values["employee_id"])
        self._validate_relationships(
            int(values["customer_id"]), int(values["project_id"]), int(values["site_id"])
        )
        day_basis = int(bool(values.get("day_basis", False)))
        day_rate = float(values.get("day_rate", 0) or 0) if day_basis else 0.0
        payment_completed = (
            int(bool(values.get("payment_completed", False))) if day_basis else 0
        )
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    UPDATE deployments
                    SET work_date = ?, employee_id = ?, customer_id = ?,
                        project_id = ?, site_id = ?, start_time = ?, end_time = ?,
                        work_type = ?, status = ?, day_basis = ?, day_rate = ?,
                        payment_completed = ?, notes = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        values["work_date"],
                        employee_id,
                        values["customer_id"],
                        values["project_id"],
                        values["site_id"],
                        values.get("start_time", "09:00"),
                        values.get("end_time", "18:00"),
                        values.get("work_type", "Full day"),
                        values.get("status", "Scheduled"),
                        day_basis,
                        day_rate,
                        payment_completed,
                        values.get("notes", "").strip(),
                        utc_now(),
                        deployment_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise ValueError("The selected deployment no longer exists.")
        except sqlite3.IntegrityError as exc:
            raise ValueError("An identical deployment already exists.") from exc

    def delete_deployment(self, deployment_id: int) -> None:
        self.connection.execute("DELETE FROM deployments WHERE id = ?", (deployment_id,))
        self.connection.commit()

    def get_deployment(self, deployment_id: int) -> dict[str, Any] | None:
        rows = self.list_deployments(deployment_id=deployment_id)
        return rows[0] if rows else None

    def list_deployments(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        employee_id: int | None = None,
        customer_id: int | None = None,
        project_id: int | None = None,
        site_id: int | None = None,
        status: str | None = None,
        day_basis: bool | None = None,
        payment_completed: bool | None = None,
        search: str = "",
        deployment_id: int | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = []

        filters = (
            ("d.work_date >= ?", date_from),
            ("d.work_date <= ?", date_to),
            ("d.employee_id = ?", employee_id),
            ("d.customer_id = ?", customer_id),
            ("d.project_id = ?", project_id),
            ("d.site_id = ?", site_id),
            ("d.status = ?", status),
            ("d.day_basis = ?", None if day_basis is None else int(day_basis)),
            (
                "d.payment_completed = ?",
                None if payment_completed is None else int(payment_completed),
            ),
            ("d.id = ?", deployment_id),
        )
        for clause, value in filters:
            if value not in (None, ""):
                conditions.append(clause)
                params.append(value)

        search = search.strip()
        if search:
            needle = f"%{search}%"
            conditions.append(
                """
                (e.name LIKE ? OR c.name LIKE ? OR p.name LIKE ? OR
                 p.project_code LIKE ? OR s.name LIKE ? OR s.city LIKE ? OR
                 d.notes LIKE ?)
                """
            )
            params.extend([needle] * 7)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self.connection.execute(
            f"""
            SELECT d.*,
                   e.employee_code, e.name AS employee_name,
                   e.designation, e.color AS employee_color,
                   c.name AS customer_name,
                   p.project_code, p.name AS project_name,
                   s.name AS site_name, s.city AS site_city
            FROM deployments d
            JOIN employees e ON e.id = d.employee_id
            JOIN customers c ON c.id = d.customer_id
            JOIN projects p ON p.id = d.project_id
            JOIN sites s ON s.id = d.site_id
            {where_sql}
            ORDER BY d.work_date ASC, d.start_time ASC, e.name COLLATE NOCASE ASC
            """,
            params,
        ).fetchall()
        return self._dicts(rows)

    def month_events(self, year: int, month: int) -> dict[str, list[dict[str, Any]]]:
        """Return the full six-week grid, including adjacent-month dates."""
        first = date(year, month, 1)
        grid_start = first - timedelta(days=first.weekday())
        grid_end = grid_start + timedelta(days=41)
        rows = self.list_deployments(
            date_from=grid_start.isoformat(),
            date_to=grid_end.isoformat(),
        )
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(row["work_date"], []).append(row)
        return grouped

    def dashboard_counts(self, year: int, month: int) -> dict[str, int]:
        prefix = f"{year:04d}-{month:02d}"
        today = date.today().isoformat()
        row = self.connection.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM deployments WHERE work_date = ?) AS today,
              (SELECT COUNT(*) FROM deployments WHERE substr(work_date, 1, 7) = ?) AS month,
              (SELECT COUNT(*) FROM employees WHERE active = 1) AS employees,
              (SELECT COUNT(*) FROM customers WHERE active = 1) AS customers
            """,
            (today, prefix),
        ).fetchone()
        return dict(row) if row else {
            "today": 0, "month": 0, "employees": 0, "customers": 0
        }

    def backup_to(self, destination: str | Path) -> Path:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        backup = sqlite3.connect(str(target))
        try:
            self.connection.backup(backup)
        finally:
            backup.close()
        return target

    def import_from(self, source: str | Path) -> None:
        """Replace the database file after validating the expected schema."""
        source_path = Path(source)
        probe = sqlite3.connect(str(source_path))
        try:
            tables = {
                row[0]
                for row in probe.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
        finally:
            probe.close()
        required = {"employees", "customers", "projects", "sites", "deployments"}
        if not required.issubset(tables):
            raise ValueError("This is not a valid Deployment Desk database.")

        self.connection.close()
        shutil.copy2(source_path, self.path)
        self.connection = sqlite3.connect(str(self.path), timeout=15)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
        self.connection.execute("PRAGMA busy_timeout = 15000")
        self._create_schema()
