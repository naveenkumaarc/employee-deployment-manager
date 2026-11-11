from __future__ import annotations

from PySide6.QtGui import QColor, QPalette


# Centralized translation of the supplied DESIGN.md into Qt-friendly tokens.
# Qt style sheets do not support CSS custom properties, so APP_STYLE is rendered
# from these values once at startup. Feature code should import COLORS instead of
# embedding visual colors of its own.
THEME = {
    "color": {
        "primary": "#00643C",
        "primary_hover": "#005333",
        "primary_pressed": "#00442A",
        "primary_soft": "#E8F3EE",
        "background": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface_alt": "#F6F8F7",
        "text": "#212121",  # rgba(0, 0, 0, .87) composited over white
        "heading": "#0E0F0C",
        "muted": "#626762",
        "border": "#DADDD9",
        "border_strong": "#BABABA",
        "danger": "#B42318",
        "danger_soft": "#FFF1F0",
        "success": "#00643C",
        "amber": "#9A6700",
        "amber_soft": "#FFF8E1",
    },
    "font": {
        "family": '"Inter", "Inter Fallback", "Segoe UI", sans-serif',
        "body_px": "14px",
        "button_px": "16px",
        "heading_px": "28px",
        "weight_regular": "400",
        "weight_semibold": "600",
    },
    "radius": {"md": "8px", "pill": "9999px"},
    "spacing": {
        "xs": "10px",
        "sm": "12px",
        "md": "16px",
        "lg": "20px",
        "xl": "30px",
        "2xl": "32px",
    },
    "shadow": {"blur": 13, "offset_y": 4, "alpha": 38},
}

COLORS = {
    "primary": THEME["color"]["primary"],
    "primary_dark": THEME["color"]["primary_hover"],
    "primary_soft": THEME["color"]["primary_soft"],
    "accent": THEME["color"]["primary"],
    "teal": THEME["color"]["primary"],
    "amber": THEME["color"]["amber"],
    "amber_soft": THEME["color"]["amber_soft"],
    "background": THEME["color"]["background"],
    "surface": THEME["color"]["surface"],
    "surface_alt": THEME["color"]["surface_alt"],
    "text": THEME["color"]["text"],
    "heading": THEME["color"]["heading"],
    "muted": THEME["color"]["muted"],
    "border": THEME["color"]["border"],
    "border_strong": THEME["color"]["border_strong"],
    "danger": THEME["color"]["danger"],
    "danger_soft": THEME["color"]["danger_soft"],
    "success": THEME["color"]["success"],
}


def _render_style() -> str:
    tokens = {
        **{f"color_{key}": value for key, value in THEME["color"].items()},
        **{f"font_{key}": value for key, value in THEME["font"].items()},
        **{f"radius_{key}": value for key, value in THEME["radius"].items()},
        **{f"space_{key}": value for key, value in THEME["spacing"].items()},
    }
    style = r"""
* {
    font-family: @font_family;
    font-size: @font_body_px;
    font-weight: @font_weight_regular;
    color: @color_text;
}
QMainWindow, QDialog, QWidget#AppRoot { background: @color_background; }
QWidget { outline: none; }
QFrame#Sidebar { background: @color_primary; border: none; }
QLabel#BrandTitle {
    color: white;
    font-size: 20px;
    font-weight: @font_weight_semibold;
}
QLabel#BrandSub, QLabel#SidebarMuted { color: #D9ECE4; font-size: 12px; }
QFrame#SidebarStat {
    background: #18734F;
    border: 1px solid #318264;
    border-radius: @radius_md;
}
QLabel#SidebarStatValue {
    color: white;
    font-size: 20px;
    font-weight: @font_weight_semibold;
    background: transparent;
}
QLabel#SidebarStatCaption { color: #D9ECE4; background: transparent; }
QLabel#PageTitle {
    color: @color_heading;
    font-size: @font_heading_px;
    font-weight: @font_weight_semibold;
}
QLabel#PageSubtitle, QLabel#Muted { color: @color_muted; }
QLabel#SectionTitle {
    color: @color_heading;
    font-size: 18px;
    font-weight: @font_weight_semibold;
}
QLabel#MetricValue {
    color: @color_heading;
    font-size: 28px;
    font-weight: @font_weight_semibold;
}
QLabel#PaidBadge {
    color: white;
    background: @color_primary;
    border-radius: @radius_pill;
    padding: 4px 10px;
    font-weight: @font_weight_semibold;
}
QLabel#PendingBadge {
    color: @color_amber;
    background: @color_amber_soft;
    border-radius: @radius_pill;
    padding: 4px 10px;
    font-weight: @font_weight_semibold;
}
QLabel#PaidText { color: @color_success; font-weight: @font_weight_semibold; }
QLabel#PendingText { color: @color_amber; font-weight: @font_weight_semibold; }
QFrame#Card, QFrame#ToolbarCard, QFrame#MetricCard {
    background: @color_surface;
    border: 1px solid @color_border_strong;
    border-radius: @radius_md;
}
QFrame#PaymentPanel {
    background: @color_surface_alt;
    border: 1px solid @color_border;
    border-radius: @radius_md;
}
QPushButton {
    min-height: 46px;
    padding: 0 @space_lg;
    border: 1px solid @color_border_strong;
    border-radius: @radius_md;
    background: @color_surface;
    color: @color_heading;
    font-size: @font_button_px;
    font-weight: @font_weight_semibold;
}
QPushButton:hover { background: @color_surface_alt; border-color: @color_primary; }
QPushButton:pressed { background: @color_primary_soft; }
QPushButton:disabled {
    color: #9A9D99;
    background: #F2F3F2;
    border-color: @color_border;
}
QPushButton#Primary {
    background: @color_primary;
    color: white;
    border-color: @color_primary;
}
QPushButton#Primary:hover {
    background: @color_primary_hover;
    border-color: @color_primary_hover;
}
QPushButton#Primary:pressed { background: @color_primary_pressed; }
QPushButton#Accent { background: white; color: @color_primary; border-color: white; }
QPushButton#Accent:hover {
    background: @color_primary_soft;
    border-color: @color_primary_soft;
}
QPushButton#Danger {
    color: @color_danger;
    background: @color_danger_soft;
    border-color: #F3B8B3;
}
QPushButton#NavButton {
    text-align: left;
    padding-left: @space_md;
    min-height: 46px;
    border: none;
    background: transparent;
    color: #E8F3EE;
    border-radius: @radius_md;
}
QPushButton#NavButton:hover { color: white; background: #18734F; }
QPushButton#NavButton:checked { color: @color_primary; background: white; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QTimeEdit,
QDoubleSpinBox {
    background: @color_surface;
    border: 1px solid @color_border_strong;
    border-radius: @radius_md;
    padding: 8px @space_sm;
    min-height: 28px;
    selection-background-color: @color_primary;
    selection-color: white;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QDateEdit:focus, QTimeEdit:focus, QDoubleSpinBox:focus {
    border: 2px solid @color_primary;
    padding: 7px 11px;
}
QComboBox::drop-down { border: none; width: 30px; }
QDateEdit { padding-right: 42px; }
QDateEdit:focus { padding: 7px 41px 7px 11px; }
QDateEdit::drop-down {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 38px;
    background: @color_primary_soft;
    border: none;
    border-left: 1px solid @color_border;
    border-top-right-radius: @radius_md;
    border-bottom-right-radius: @radius_md;
}
QDateEdit::drop-down:hover { background: #D7EADF; }
QDateEdit::down-arrow { image: none; width: 0; height: 0; }
QTimeEdit::up-button, QTimeEdit::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 0; height: 0; border: none;
}
QCheckBox { spacing: @space_xs; }
QCheckBox::indicator, QListView::indicator, QListWidget::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid @color_primary;
    border-radius: 4px;
    background: white;
}
QCheckBox::indicator:hover, QListView::indicator:hover,
QListWidget::indicator:hover { background: @color_primary_soft; }
QCheckBox::indicator:checked, QListView::indicator:checked,
QListWidget::indicator:checked {
    background: @color_primary;
    border-color: @color_primary;
    image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-apply-16.png);
}
QComboBox QAbstractItemView, QListView#ComboPopup {
    background: white;
    color: @color_text;
    border: 1px solid @color_border_strong;
    border-radius: @radius_md;
    padding: 5px;
    selection-background-color: @color_primary_soft;
    selection-color: @color_heading;
}
QComboBox QAbstractItemView::item, QListView#ComboPopup::item {
    min-height: 34px;
    padding: 5px @space_xs;
    border-radius: 6px;
}
QComboBox QAbstractItemView::item:hover, QListView#ComboPopup::item:hover {
    background: @color_primary_soft;
}
QListWidget, QTableWidget, QTableView {
    background: white;
    alternate-background-color: @color_surface_alt;
    border: 1px solid @color_border_strong;
    border-radius: @radius_md;
    gridline-color: @color_border;
    selection-background-color: @color_primary_soft;
    selection-color: @color_heading;
}
QListWidget::item { padding: 8px; border-radius: 6px; }
QListWidget::item:selected { background: @color_primary_soft; color: @color_heading; }
QHeaderView::section {
    background: @color_surface_alt;
    color: @color_muted;
    border: none;
    border-bottom: 1px solid @color_border;
    padding: 10px 8px;
    font-weight: @font_weight_semibold;
}
QTableWidget::item { padding: 7px; }
QTabWidget::pane {
    background: white;
    border: 1px solid @color_border_strong;
    border-radius: @radius_md;
    top: -1px;
}
QTabBar::tab {
    padding: 10px 18px;
    margin-right: 4px;
    color: @color_muted;
    background: @color_surface_alt;
    border-radius: @radius_md;
}
QTabBar::tab:selected { color: white; background: @color_primary; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 12px; margin: 4px 2px; }
QScrollBar::handle:vertical {
    background: #A8B8B0; min-height: 38px; border-radius: 5px;
}
QScrollBar::handle:vertical:hover { background: @color_primary; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0; background: transparent;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 2px 4px; }
QScrollBar::handle:horizontal {
    background: #A8B8B0; min-width: 38px; border-radius: 5px;
}
QScrollBar::handle:horizontal:hover { background: @color_primary; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0; background: transparent;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QStatusBar {
    background: white;
    color: @color_muted;
    border-top: 1px solid @color_border;
}
QToolTip {
    background: @color_heading;
    color: white;
    border: none;
    border-radius: @radius_md;
    padding: 6px;
}
QMessageBox, QFileDialog { background: white; }
QMessageBox QLabel { color: @color_text; }
QCalendarWidget QWidget { background: white; color: @color_text; }
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: @color_primary; min-height: 42px;
}
QCalendarWidget QToolButton {
    color: white;
    background: transparent;
    border: none;
    border-radius: @radius_md;
    min-height: 30px;
    padding: 4px @space_xs;
}
QCalendarWidget QToolButton:hover { background: rgba(255, 255, 255, 38); }
QCalendarWidget QSpinBox {
    color: white;
    background: @color_primary_hover;
    selection-background-color: white;
    selection-color: @color_heading;
}
QCalendarWidget QAbstractItemView {
    background: white;
    color: @color_text;
    alternate-background-color: white;
    selection-background-color: @color_primary;
    selection-color: white;
    border: none;
}
QCalendarWidget QAbstractItemView:disabled { color: #9A9D99; }
"""
    for name, value in tokens.items():
        style = style.replace(f"@{name}", str(value))
    return style


APP_STYLE = _render_style()


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
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS["heading"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
    return palette
