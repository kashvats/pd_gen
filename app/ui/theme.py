"""Dark modern studio styling, typography, and QSS stylesheets."""

STUDIO_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #121316;
    color: #E2E8F0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #27272A;
    background-color: #18181B;
    border-radius: 6px;
}

QTabBar::tab {
    background: #1E1E24;
    color: #A1A1AA;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #27272A;
    color: #F4F4F5;
    border-bottom: 2px solid #6366F1;
}

QTabBar::tab:hover {
    background: #232329;
    color: #E4E4E7;
}

QGroupBox {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    font-weight: 600;
    color: #E4E4E7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    background-color: #18181B;
    border-radius: 4px;
    color: #A5B4FC;
}

QPushButton {
    background-color: #27272A;
    color: #F4F4F5;
    border: 1px solid #3F3F46;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3F3F46;
    border-color: #52525B;
}

QPushButton:pressed {
    background-color: #18181B;
}

QPushButton:disabled {
    background-color: #1A1A1E;
    color: #52525B;
    border-color: #27272A;
}

QPushButton#PrimaryButton {
    background-color: #4F46E5;
    color: #FFFFFF;
    border: 1px solid #6366F1;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background-color: #4338CA;
    border-color: #818CF8;
}

QPushButton#PrimaryButton:pressed {
    background-color: #3730A3;
}

QPushButton#AccentButton {
    background-color: #059669;
    color: #FFFFFF;
    border: 1px solid #10B981;
    font-weight: 600;
}

QPushButton#AccentButton:hover {
    background-color: #047857;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #09090B;
    color: #F4F4F5;
    border: 1px solid #27272A;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #4F46E5;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #6366F1;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #27272A;
}

QComboBox QAbstractItemView {
    background-color: #18181B;
    border: 1px solid #3F3F46;
    selection-background-color: #4F46E5;
    selection-color: #FFFFFF;
    padding: 4px;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #27272A;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #6366F1;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 1px solid #A5B4FC;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #E0E7FF;
}

QProgressBar {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 6px;
    text-align: center;
    color: #F4F4F5;
    font-weight: 600;
    height: 18px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #10B981);
    border-radius: 5px;
}

QScrollBar:vertical {
    border: none;
    background: #121316;
    width: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #27272A;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #3F3F46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QSplitter::handle {
    background-color: #27272A;
}

QSplitter::handle:hover {
    background-color: #6366F1;
}

QTableWidget, QListWidget {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 6px;
    gridline-color: #27272A;
}

QHeaderView::section {
    background-color: #121316;
    color: #A1A1AA;
    padding: 6px;
    border: 1px solid #27272A;
    font-weight: 600;
}
"""


def apply_studio_theme(app):
    """Applies the studio dark theme to the Qt application."""
    app.setStyleSheet(STUDIO_QSS)
