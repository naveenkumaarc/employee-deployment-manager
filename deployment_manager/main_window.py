from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDate, QSize, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__
from .database import Database
from .dialogs import DeploymentDialog, DirectoryDialog
from .icons import app_icon
from .pages import CalendarPage, HistoryPage, ReportsPage
from .theme import COLORS
from .widgets import make_button


class MainWindow(QMainWindow):
    def __init__(
        self,
        database: Database,
        app_data_directory: Path,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.database = database
        self.app_data_directory = app_data_directory
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(1480, 900)
        self.setMinimumSize(1180, 720)

        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        root_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.calendar_page = CalendarPage(database)
        self.history_page = HistoryPage(database)
        self.reports_page = ReportsPage(database)
        self.stack.addWidget(self.calendar_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.reports_page)
        root_layout.addWidget(self.stack, 1)

        self.calendar_page.dataChanged.connect(self.refresh_all)
        self.calendar_page.requestDirectory.connect(self.open_directory)
        self.history_page.dataChanged.connect(self.refresh_all)

        self._wire_navigation()
        self._create_shortcuts()
        self.refresh_all()
        self.show_page(0)
        self.statusBar().showMessage(
            f"Database: {self.database.path}  •  Deployment Desk {__version__}"
        )

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(286)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(22, 23, 22, 20)
        layout.setSpacing(10)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        icon_label = QLabel()
        icon_label.setPixmap(app_icon().pixmap(QSize(48, 48)))
        icon_label.setFixedSize(52, 52)
        brand_row.addWidget(icon_label)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand = QLabel("Deployment Desk")
        brand.setObjectName("BrandTitle")
        brand.setMinimumWidth(170)
        sub = QLabel("FIELD TEAM PLANNING")
        sub.setObjectName("BrandSub")
        brand_text.addWidget(brand)
        brand_text.addWidget(sub)
        brand_row.addLayout(brand_text, 1)
        layout.addLayout(brand_row)
        layout.addSpacing(17)

        new_button = make_button("＋  Create deployment", role="Accent")
        new_button.setMinimumHeight(47)
        new_button.clicked.connect(self.open_new_deployment)
        layout.addWidget(new_button)
        layout.addSpacing(7)

        section = QLabel("WORKSPACE")
        section.setObjectName("SidebarMuted")
        layout.addWidget(section)

        self.calendar_nav = make_button("▦   Calendar", role="NavButton", checkable=True)
        self.history_nav = make_button("↺   History", role="NavButton", checkable=True)
        self.reports_nav = make_button("▥   Reports", role="NavButton", checkable=True)
        self.directory_nav = make_button("♙   Employees && directory", role="NavButton")
        layout.addWidget(self.calendar_nav)
        layout.addWidget(self.history_nav)
        layout.addWidget(self.reports_nav)
        layout.addWidget(self.directory_nav)

        layout.addSpacing(18)
        section = QLabel("CURRENT MONTH")
        section.setObjectName("SidebarMuted")
        layout.addWidget(section)

        self.month_count = self._sidebar_stat("0", "deployments")
        self.people_count = self._sidebar_stat("0", "active employees")
        self.today_count = self._sidebar_stat("0", "today")
        layout.addWidget(self.month_count[0])
        layout.addWidget(self.people_count[0])
        layout.addWidget(self.today_count[0])

        layout.addStretch()

        backup = make_button("Back up database")
        backup.setStyleSheet(
            "QPushButton { color:#5D252C; background:#E8A8AE; border:none; }"
            "QPushButton:hover { background:#DB9198; color:#4F1F25; }"
        )
        backup.clicked.connect(self.backup_database)
        layout.addWidget(backup)

        footer = QLabel("Local SQLite data • No cloud required")
        footer.setObjectName("SidebarMuted")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        return sidebar

    def _sidebar_stat(self, value: str, caption: str) -> tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background:#E8A8AE; border-radius:11px; }"
            "QLabel { background:transparent; }"
        )
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(13, 8, 13, 8)
        value_label = QLabel(value)
        value_label.setStyleSheet(
            "color:#5D252C; font-size:16pt; font-weight:750; background:transparent;"
        )
        caption_label = QLabel(caption)
        caption_label.setStyleSheet(
            "color:#73363D; background:transparent; font-size:9pt;"
        )
        frame_layout.addWidget(value_label)
        frame_layout.addWidget(caption_label, 1)
        return frame, value_label

    def _wire_navigation(self) -> None:
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for index, button in enumerate(
            (self.calendar_nav, self.history_nav, self.reports_nav)
        ):
            self.nav_group.addButton(button, index)
            button.clicked.connect(
                lambda _checked=False, page=index: self.show_page(page)
            )
        self.directory_nav.clicked.connect(self.open_directory)

    def _create_shortcuts(self) -> None:
        actions = (
            ("New deployment", QKeySequence("Ctrl+N"), self.open_new_deployment),
            ("Calendar", QKeySequence("Ctrl+1"), lambda: self.show_page(0)),
            ("History", QKeySequence("Ctrl+2"), lambda: self.show_page(1)),
            ("Reports", QKeySequence("Ctrl+3"), lambda: self.show_page(2)),
            ("Directory", QKeySequence("Ctrl+D"), self.open_directory),
        )
        for text, shortcut, callback in actions:
            action = QAction(text, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    def show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)
        if index == 0:
            self.calendar_page.refresh()
        elif index == 1:
            self.history_page.refresh_options()
            self.history_page.refresh()
        elif index == 2:
            self.reports_page.refresh_options()
            self.reports_page.generate()

    def open_new_deployment(self) -> None:
        if not self.database.required_data_ready():
            answer = QMessageBox.information(
                self,
                "Directory setup required",
                "Before scheduling work, add an employee, customer, project and site.\n\n"
                "The directory will open now.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Ok,
            )
            if answer == QMessageBox.StandardButton.Ok:
                self.open_directory()
            return
        initial = (
            self.calendar_page.calendar.selectedDate()
            if self.stack.currentWidget() is self.calendar_page
            else QDate.currentDate()
        )
        if DeploymentDialog(
            self.database, initial_date=initial, parent=self
        ).exec():
            self.refresh_all()
            self.show_page(0)

    def open_directory(self) -> None:
        DirectoryDialog(self.database, self).exec()
        self.refresh_all()

    def refresh_all(self) -> None:
        self.calendar_page.refresh()
        self.history_page.refresh_options()
        self.history_page.refresh()
        self.reports_page.refresh_options()
        counts = self.database.dashboard_counts(
            self.calendar_page.calendar.yearShown(),
            self.calendar_page.calendar.monthShown(),
        )
        self.month_count[1].setText(str(counts["month"]))
        self.people_count[1].setText(str(counts["employees"]))
        self.today_count[1].setText(str(counts["today"]))

    def backup_database(self) -> None:
        default = (
            Path.home()
            / "Documents"
            / f"DeploymentDesk_Backup_{datetime.now():%Y%m%d_%H%M}.db"
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Back up Deployment Desk database",
            str(default),
            "SQLite database (*.db)",
        )
        if not path:
            return
        if not path.lower().endswith(".db"):
            path += ".db"
        try:
            self.database.backup_to(path)
        except OSError as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))
            return
        QMessageBox.information(
            self,
            "Backup complete",
            f"Database backup saved successfully:\n\n{path}",
        )
