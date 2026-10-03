# Deployment Desk

![Deployment Desk rounded-square icon](assets/app_icon.png)

Deployment Desk is a modern, offline employee deployment manager built with Python and PySide6. It keeps field-team assignments clear on a large Google Calendar-style month view and creates useful Excel reports without requiring a cloud service.

## What it does

- Shows roughly three quarters of the window as a large monthly deployment calendar.
- Opens a new deployment form when you click an empty date.
- Opens that day's assignments when you click a date that already has entries.
- Copies an existing deployment to another date while keeping the original record.
- Assigns one or many employees to a customer, project and site in one step.
- Records optional day-basis work, an amount per employee per day, and whether
  that payment is completed or pending.
- Warns when an employee already has another deployment on the selected date.
- Maintains employee, customer, project and site directories.
- Provides searchable, filterable history with edit and delete actions.
- Generates employee-wise, month-wise, date-wise, project-wise and customer-wise
  deployment and payment reports for any custom date range.
- Filters history and reports by pending or completed payment status.
- Exports formatted summary and detailed worksheets to Excel.
- Stores data locally in SQLite and includes a one-click database backup.
- Opens maximized with a polished pastel-red SoftMaterial interface and a
  matching transparent rounded-square icon.
- Prevents accidental mouse-wheel changes in date, time, amount and selection fields.

## Start on Windows

You need Python 3.10 or newer.

1. Clone this repository or download and extract its ZIP.
2. Double-click **run_windows.bat**.
3. On the first run, it creates a private virtual environment and installs the required packages.
4. In Deployment Desk, open **Employees & directory** and add data in this order:
   employee, customer, project, site.
5. Return to the calendar and click a date to schedule work.

From a terminal, the same setup is:

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

## Download the Windows executable

A fresh Windows executable is built automatically for every update to `main`.

1. Open the repository's **Actions** tab.
2. Select **Build Windows app**.
3. Open the latest successful run.
4. Download the **DeploymentDesk-Windows** artifact.
5. Extract the ZIP and run `DeploymentDesk.exe`.

The executable is self-contained; Python is not required on the destination PC.

## Everyday workflow

- **Create deployment:** use the coral button in the left sidebar, or press `Ctrl+N`.
- **Calendar:** click an empty date to add work; click a populated date to review,
  copy, edit, delete or add more.
- **History:** filter by date, employee, customer, project, site, status or payment;
  select a row and use **Copy selected** to schedule the same work on a new date.
- **Reports:** choose a grouping and any date range, review total/completed/pending
  day-basis amounts, then export the full report to `.xlsx`.
- **Directory:** deactivate old employees, customers, projects or sites without losing historical records.
- **Backup:** use **Back up database** in the sidebar. The exact live database path is shown in the status bar.

Keyboard shortcuts: `Ctrl+1` calendar, `Ctrl+2` history, `Ctrl+3` reports, and `Ctrl+D` directory.

## Build the Windows executable yourself

Double-click **build_windows.bat**, or run:

```powershell
python -m pip install -r requirements-dev.txt
python tools\generate_icons.py
python -m pytest -q
python -m PyInstaller --noconfirm --clean DeploymentDesk.spec
```

The result is `dist\DeploymentDesk.exe`.

## Data and privacy

All operational data is stored in a local SQLite database. Deployment Desk does not send employee, customer or project information to any external service. Keep regular copies using the built-in backup command, especially before moving to a new computer.

## Technology

- Python 3.10+
- PySide6 / Qt 6
- SQLite
- openpyxl
- PyInstaller
