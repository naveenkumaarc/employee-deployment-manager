from __future__ import annotations

from typing import Any, Iterable

from PySide6.QtCore import QDate, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCalendarWidget,
    QComboBox,
    QDateEdit,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from .theme import COLORS


def make_button(
    text: str,
    *,
    role: str = "",
    checkable: bool = False,
    tooltip: str = "",
) -> QPushButton:
    button = QPushButton(text)
    if role:
        button.setObjectName(role)
    button.setCheckable(checkable)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setAutoDefault(False)
    if tooltip:
        button.setToolTip(tooltip)
    return button


def set_combo_value(combo: QComboBox, value: Any) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)


def fill_combo(
    combo: QComboBox,
    rows: Iterable[dict[str, Any]],
    *,
    include_all: bool = False,
    all_label: str = "All",
    label_key: str = "name",
) -> None:
    previous = combo.currentData()
    combo.blockSignals(True)
    combo.clear()
    if include_all:
        combo.addItem(all_label, None)
    for row in rows:
        label = str(row.get(label_key, ""))
        combo.addItem(label, row.get("id"))
    set_combo_value(combo, previous)
    combo.blockSignals(False)


def make_date_edit(value: QDate | None = None) -> QDateEdit:
    edit = QDateEdit(value or QDate.currentDate())
    edit.setCalendarPopup(True)
    edit.setDisplayFormat("dd MMM yyyy")
    edit.setMinimumWidth(145)
    calendar = edit.calendarWidget()
    calendar.setGridVisible(False)
    calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
    calendar.setHorizontalHeaderFormat(
        QCalendarWidget.HorizontalHeaderFormat.ShortDayNames
    )
    return edit


def make_table(columns: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(False)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(
        len(columns) - 1, QHeaderView.ResizeMode.Stretch
    )
    return table


def add_soft_shadow(widget: QWidget, radius: int = 24, opacity: int = 25) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(radius)
    shadow.setOffset(0, 6)
    shadow.setColor(QColor(23, 32, 51, opacity))
    widget.setGraphicsEffect(shadow)


class PageHeading(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        layout.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("PageSubtitle")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)


class MetricCard(QFrame):
    def __init__(
        self,
        label: str,
        value: str = "0",
        accent: str = "#526DFE",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setMinimumHeight(92)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)

        bar = QFrame()
        bar.setFixedWidth(5)
        bar.setStyleSheet(f"background: {accent}; border-radius: 2px;")
        layout.addWidget(bar)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        label_widget = QLabel(label)
        label_widget.setObjectName("Muted")
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(label_widget)
        layout.addLayout(text_layout, 1)

    def set_value(self, value: int | str) -> None:
        self.value_label.setText(str(value))


class SearchBox(QLineEdit):
    def __init__(self, placeholder: str = "Search", parent: QWidget | None = None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setMinimumWidth(220)


class MonthCalendar(QCalendarWidget):
    """Large month grid that paints deployment chips directly in each day."""

    pageChanged = Signal(int, int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._events: dict[str, list[dict[str, Any]]] = {}
        self.setNavigationBarVisible(False)
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.setHorizontalHeaderFormat(
            QCalendarWidget.HorizontalHeaderFormat.ShortDayNames
        )
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setMinimumHeight(620)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.currentPageChanged.connect(self._emit_page_changed)
        self.setStyleSheet(
            """
            QCalendarWidget {
                background: white;
                border: 1px solid #E3E9F2;
                border-radius: 16px;
            }
            QCalendarWidget QAbstractItemView {
                background: white;
                color: #172033;
                selection-background-color: transparent;
                selection-color: #172033;
                border: none;
                font-weight: 650;
            }
            QCalendarWidget QHeaderView::section {
                background: #F4F7FB;
                color: #526075;
                min-height: 35px;
                border: none;
                border-bottom: 1px solid #E3E9F2;
                font-weight: 700;
            }
            """
        )

    def _emit_page_changed(self, year: int, month: int) -> None:
        self.pageChanged.emit(year, month)

    def set_events(self, events: dict[str, list[dict[str, Any]]]) -> None:
        self._events = events
        self.updateCells()

    def events_for(self, value: QDate) -> list[dict[str, Any]]:
        return self._events.get(value.toString("yyyy-MM-dd"), [])

    def paintCell(self, painter: QPainter, rect: QRect, value: QDate) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        in_month = (
            value.year() == self.yearShown() and value.month() == self.monthShown()
        )
        selected = value == self.selectedDate()
        today = value == QDate.currentDate()

        background = QColor("#FFFFFF") if in_month else QColor("#F7F9FC")
        if selected:
            background = QColor(COLORS["primary_soft"])
        painter.fillRect(rect, background)
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        day_font = painter.font()
        day_font.setPointSize(9)
        day_font.setBold(True)
        painter.setFont(day_font)

        day_box = QRect(rect.left() + 8, rect.top() + 5, 28, 22)
        if today:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLORS["primary"]))
            painter.drawEllipse(day_box.adjusted(2, 0, -4, 0))
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(
                day_box.adjusted(0, 0, -2, 0),
                Qt.AlignmentFlag.AlignCenter,
                str(value.day()),
            )
        else:
            if not in_month:
                number_color = QColor("#AAB4C4")
            elif value.dayOfWeek() == Qt.DayOfWeek.Sunday:
                number_color = QColor(COLORS["accent"])
            else:
                number_color = QColor(COLORS["text"])
            painter.setPen(number_color)
            painter.drawText(
                day_box,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(value.day()),
            )

        events = self.events_for(value)
        available = max(1, (rect.height() - 37) // 21)
        visible_count = min(len(events), max(0, available - (1 if len(events) > available else 0)))
        chip_font = painter.font()
        chip_font.setPointSize(8)
        chip_font.setBold(False)
        painter.setFont(chip_font)
        metrics = QFontMetrics(chip_font)

        y = rect.top() + 30
        for event in events[:visible_count]:
            chip = QRect(rect.left() + 6, y, max(20, rect.width() - 12), 18)
            color = QColor(event.get("employee_color") or COLORS["primary"])
            if event.get("status") == "Cancelled":
                color = QColor("#9AA6B7")
            soft = QColor(color)
            soft.setAlpha(42)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(soft)
            painter.drawRoundedRect(chip, 5, 5)
            painter.setBrush(color)
            painter.drawRoundedRect(QRect(chip.left(), chip.top(), 4, chip.height()), 2, 2)

            label = f"{event.get('employee_name', '')} · {event.get('project_name', '')}"
            text_rect = chip.adjusted(9, 0, -5, 0)
            label = metrics.elidedText(
                label, Qt.TextElideMode.ElideRight, text_rect.width()
            )
            painter.setPen(QColor("#27344A"))
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                label,
            )
            y += 21

        remaining = len(events) - visible_count
        if remaining > 0:
            painter.setPen(QColor(COLORS["primary"]))
            overflow_font = painter.font()
            overflow_font.setBold(True)
            painter.setFont(overflow_font)
            painter.drawText(
                QRect(rect.left() + 8, y, rect.width() - 16, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"+{remaining} more",
            )

        if selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(COLORS["primary"]), 2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -2, -2), 7, 7)

        painter.restore()
