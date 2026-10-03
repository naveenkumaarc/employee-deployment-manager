from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

COLORS = {
    "primary": "#D86F78",
    "primary_dark": "#B94F5A",
    "primary_soft": "#FCEBED",
    "accent": "#C44F5B",
    "teal": "#19B8A4",
    "amber": "#F3A83B",
    "background": "#F4F7FB",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFD",
    "text": "#172033",
    "muted": "#68758A",
    "border": "#E3E9F2",
    "danger": "#D84B5B",
    "success": "#14947E",
}

APP_STYLE = r"""
* {
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
    color: #172033;
}
QMainWindow, QDialog, QWidget#AppRoot {
    background: #F4F7FB;
}
QWidget {
    outline: none;
}
QFrame#Sidebar {
    background: #F5CDD1;
    border: none;
}
QLabel#BrandTitle {
    color: #5D252C;
    font-size: 16pt;
    font-weight: 700;
}
QLabel#BrandSub, QLabel#SidebarMuted {
    color: #875159;
}
QLabel#PageTitle {
    color: #172033;
    font-size: 21pt;
    font-weight: 700;
}
QLabel#PageSubtitle, QLabel#Muted {
    color: #68758A;
}
QLabel#SectionTitle {
    font-size: 12pt;
    font-weight: 700;
}
QLabel#MetricValue {
    font-size: 20pt;
    font-weight: 750;
}
QFrame#Card, QFrame#ToolbarCard, QFrame#MetricCard {
    background: white;
    border: 1px solid #E3E9F2;
    border-radius: 16px;
}
QFrame#PaymentPanel {
    background: #FFF8F8;
    border: 1px solid #F1DADD;
    border-radius: 11px;
}
QPushButton {
    min-height: 38px;
    padding: 0 15px;
    border: 1px solid #DDE4EE;
    border-radius: 10px;
    background: white;
    color: #27344A;
    font-weight: 600;
}
QPushButton:hover {
    background: #F2F5FA;
    border-color: #C9D3E2;
}
QPushButton:pressed {
    background: #E9EEF6;
}
QPushButton:disabled {
    color: #A9B1BE;
    background: #F3F5F8;
}
QPushButton#Primary {
    background: #D86F78;
    color: white;
    border-color: #D86F78;
}
QPushButton#Primary:hover {
    background: #C75F69;
}
QPushButton#Accent {
    background: #FFF8F9;
    color: #743039;
    border-color: #FFF8F9;
}
QPushButton#Accent:hover {
    background: #FCEAEC;
    border-color: #FCEAEC;
}
QPushButton#Danger {
    color: #C83E50;
    background: #FFF3F4;
    border-color: #FFDADD;
}
QPushButton#NavButton {
    text-align: left;
    padding-left: 17px;
    min-height: 45px;
    border: none;
    background: transparent;
    color: #6F3038;
    border-radius: 11px;
}
QPushButton#NavButton:hover {
    color: #5D252C;
    background: #EDB4B9;
}
QPushButton#NavButton:checked {
    color: white;
    background: #D86F78;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QTimeEdit,
QDoubleSpinBox {
    background: white;
    border: 1px solid #DCE3ED;
    border-radius: 9px;
    padding: 7px 10px;
    min-height: 23px;
    selection-background-color: #D86F78;
    selection-color: white;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus,
QTimeEdit:focus, QDoubleSpinBox:focus {
    border: 2px solid #E79AA1;
    padding: 6px 9px;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QDateEdit {
    padding-right: 42px;
}
QDateEdit:focus {
    padding: 6px 41px 6px 9px;
}
QDateEdit::drop-down {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 38px;
    background: #FCEBED;
    border: none;
    border-left: 1px solid #EECFD3;
    border-top-right-radius: 9px;
    border-bottom-right-radius: 9px;
}
QDateEdit::drop-down:hover {
    background: #F7DADD;
}
QDateEdit::down-arrow {
    image: none;
    width: 0;
    height: 0;
}
QTimeEdit::up-button, QTimeEdit::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 0;
    height: 0;
    border: none;
}
QCheckBox {
    spacing: 9px;
}
QCheckBox::indicator, QListView::indicator, QListWidget::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #C65C66;
    border-radius: 5px;
    background: white;
}
QCheckBox::indicator:hover, QListView::indicator:hover,
QListWidget::indicator:hover {
    border-color: #A9434E;
    background: #FFF5F6;
}
QCheckBox::indicator:checked, QListView::indicator:checked,
QListWidget::indicator:checked {
    background: #D86F78;
    border-color: #B94F5A;
    image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-apply-16.png);
}
QComboBox QAbstractItemView {
    background: white;
    color: #172033;
    border: 1px solid #DCE3ED;
    selection-background-color: #FCEBED;
    selection-color: #172033;
    padding: 5px;
}
QComboBox QAbstractItemView::item {
    min-height: 34px;
    padding: 5px 10px;
    border-radius: 7px;
}
QComboBox QAbstractItemView::item:hover {
    background: #FFF1F2;
}
QListView#ComboPopup {
    background: white;
    color: #172033;
    border: 1px solid #DCE3ED;
    border-radius: 10px;
    padding: 5px;
    selection-background-color: #FCEBED;
    selection-color: #172033;
}
QListView#ComboPopup::item {
    min-height: 34px;
    padding: 5px 10px;
    border-radius: 7px;
}
QListView#ComboPopup::item:hover {
    background: #FFF1F2;
}
QListWidget, QTableWidget, QTableView {
    background: white;
    alternate-background-color: #F8FAFD;
    border: 1px solid #E3E9F2;
    border-radius: 11px;
    gridline-color: #EDF1F6;
    selection-background-color: #FCEBED;
    selection-color: #172033;
}
QListWidget::item {
    padding: 8px;
    border-radius: 7px;
}
QListWidget::item:selected {
    background: #FCEBED;
    color: #172033;
}
QHeaderView::section {
    background: #F4F7FB;
    color: #536177;
    border: none;
    border-bottom: 1px solid #DCE3ED;
    padding: 9px 7px;
    font-weight: 700;
}
QTableWidget::item {
    padding: 6px;
}
QTabWidget::pane {
    background: white;
    border: 1px solid #E3E9F2;
    border-radius: 12px;
    top: -1px;
}
QTabBar::tab {
    padding: 10px 18px;
    margin-right: 4px;
    color: #68758A;
    background: #EDF1F6;
    border-radius: 9px;
}
QTabBar::tab:selected {
    color: white;
    background: #D86F78;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 14px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #D9A5AA;
    min-height: 38px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #BE737B;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: transparent;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: transparent;
    height: 14px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background: #D9A5AA;
    min-width: 38px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #BE737B;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: transparent;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}
QStatusBar {
    background: white;
    color: #68758A;
    border-top: 1px solid #E3E9F2;
}
QToolTip {
    background: #73323A;
    color: white;
    border: none;
    padding: 6px;
}
QMessageBox, QFileDialog {
    background: #F4F7FB;
}
QMessageBox QLabel {
    color: #172033;
}
QCalendarWidget QWidget {
    background: white;
    color: #172033;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #D86F78;
    min-height: 42px;
}
QCalendarWidget QToolButton {
    color: white;
    background: transparent;
    border: none;
    border-radius: 7px;
    min-height: 30px;
    padding: 4px 10px;
}
QCalendarWidget QToolButton:hover {
    background: rgba(255, 255, 255, 38);
}
QCalendarWidget QSpinBox {
    color: white;
    background: #BE5964;
    selection-background-color: white;
    selection-color: #172033;
}
QCalendarWidget QAbstractItemView {
    background: white;
    color: #172033;
    alternate-background-color: white;
    selection-background-color: #D86F78;
    selection-color: white;
    border: none;
}
QCalendarWidget QAbstractItemView:disabled {
    color: #98A3B5;
}
"""


def application_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS["background"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS["surface_alt"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS["surface"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS["primary"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#73323A"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
    return palette
