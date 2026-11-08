from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


ICON_PATHS = {
    "open": '<path d="M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/><path d="M3 10h18"/>',
    "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M7 3v6h10V4M7 21v-8h10v8"/>',
    "find": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "text": '<path d="M4 6h16M12 6v14M8 20h8M4 6v3M20 6v3"/>',
    "highlight": '<path d="m15 4 5 5M5 19l5-1L21 7a2 2 0 0 0-4-4L6 14l-1 5ZM3 22h18"/>',
    "sign": '<path d="M2 18c4 0 7-12 9-12 3 0-4 13-2 13 2 0 3-4 5-4s2 4 4 4c2 0 2-2 4-2"/>',
    "rotate": '<path d="M3 12a9 9 0 1 0 3-7M3 4v6h6"/>',
    "compress": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 6v5M8 11H5M8 11 5 8M16 18v-5M16 13h3M16 13l3 3"/>',
}


def toolbar_icon(name: str) -> QIcon:
    paths = ICON_PATHS[name]
    markup = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="#405572" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )
    renderer = QSvgRenderer(QByteArray(markup.encode("utf-8")))
    pixmap = QPixmap(40, 40)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


APP_STYLESHEET = """
QMainWindow {
    background: #f4f6fa;
    color: #28374a;
}
QMenuBar {
    background: #ffffff;
    color: #28374a;
    border-bottom: 1px solid #e0e6ee;
    padding: 4px 6px;
}
QMenuBar::item {
    padding: 6px 10px;
    border-radius: 5px;
}
QMenuBar::item:selected {
    background: #edf3ff;
}
QMenu {
    background: #ffffff;
    border: 1px solid #dce4f0;
    padding: 5px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 5px;
}
QMenu::item:selected {
    background: #e9f1ff;
}
QToolBar#quick_access {
    background: #ffffff;
    border-bottom: 1px solid #dfe5ed;
    spacing: 4px;
    padding: 8px 10px;
}
QToolBar#quick_access QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    color: #28374a;
    font-weight: 600;
    padding: 6px 9px;
}
QToolBar#quick_access QToolButton:hover {
    background: #edf3ff;
}
QToolBar#quick_access QToolButton:checked {
    background: #e2edff;
    border-color: #8db5f4;
    color: #174f9d;
}
QToolBar#quick_access QToolButton:disabled {
    color: #a0aab9;
}
QToolBar#page_navigation {
    background: #ffffff;
    border-top: 1px solid #dfe5ed;
    padding: 4px 10px;
    spacing: 6px;
}
QToolBar#page_navigation QToolButton {
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
}
QToolBar#page_navigation QToolButton:hover {
    background: #edf3ff;
}
QTabWidget::pane {
    border: none;
}
QTabBar::tab {
    background: #e7ecf4;
    border: 1px solid #dce4ed;
    border-bottom: 0;
    border-radius: 6px 6px 0 0;
    color: #4d617c;
    margin: 4px 2px 0 0;
    min-width: 110px;
    padding: 8px 12px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #1a365d;
    font-weight: 600;
}
QDockWidget#page_thumbnails {
    color: #2b3b50;
    font-weight: 600;
}
QListWidget#page_thumbnail_list {
    background: #f8fafd;
    color: #4d617c;
    border: 0;
    border-right: 1px solid #dfe5ed;
}
QListWidget#page_thumbnail_list::item {
    background: transparent;
    border: 2px solid transparent;
    border-radius: 7px;
    margin: 3px;
    padding: 4px;
}
QListWidget#page_thumbnail_list::item:selected {
    background: #eaf2ff;
    border-color: #8bb5ee;
    color: #1b4d94;
}
QWidget#search_bar {
    background: #ffffff;
    border-bottom: 1px solid #dfe5ed;
}
QLineEdit {
    border: 1px solid #cbd6e4;
    background: #ffffff;
    color: #1e293b;
    padding: 7px 10px;
    border-radius: 6px;
}
QLineEdit:focus {
    border-color: #417ed2;
}
QPushButton#welcome_open {
    background: #2866bd;
    border: 1px solid #235bad;
    border-radius: 8px;
    color: #ffffff;
    font-weight: 600;
    padding: 10px 24px;
}
QPushButton#welcome_open:hover {
    background: #1757ae;
}
QStatusBar {
    background: #ffffff;
    color: #58677b;
    border-top: 1px solid #dfe5ed;
}
"""
