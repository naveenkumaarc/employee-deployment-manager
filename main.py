from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication, QMessageBox

from deployment_manager import APP_NAME, __version__
from deployment_manager.database import Database
from deployment_manager.icons import app_icon, write_icon_assets
from deployment_manager.main_window import MainWindow
from deployment_manager.theme import APP_STYLE, application_palette


def app_data_directory() -> Path:
    location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )
    target = Path(location or (Path.home() / "AppData" / "Local" / "DeploymentDesk"))
    target.mkdir(parents=True, exist_ok=True)
    return target


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("AMICS Automations")
    app.setStyle("Fusion")
    app.setPalette(application_palette())
    app.setStyleSheet(APP_STYLE)

    source_assets = Path(__file__).resolve().parent / "assets"
    if not getattr(sys, "frozen", False):
        try:
            write_icon_assets(source_assets, overwrite=True)
        except OSError:
            pass
    app.setWindowIcon(app_icon())

    try:
        database = Database(app_data_directory() / "deployment_desk.db")
    except Exception as exc:
        QMessageBox.critical(
            None,
            "Database error",
            f"Deployment Desk could not open its database.\n\n{exc}",
        )
        return 1

    window = MainWindow(database, app_data_directory())
    window.showMaximized()
    exit_code = app.exec()
    database.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
