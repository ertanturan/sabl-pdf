from PySide6.QtCore import QPoint, QSize, QSignalBlocker, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QDockWidget, QListView, QListWidget, QListWidgetItem, QWidget

from sabl_pdf.services.viewer import ViewerService


class PageThumbnails(QDockWidget):
    page_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Pages", parent)
        self.setObjectName("page_thumbnails")
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.pages = QListWidget(self)
        self.pages.setObjectName("page_thumbnail_list")
        self.pages.setViewMode(QListView.ViewMode.IconMode)
        self.pages.setFlow(QListView.Flow.TopToBottom)
        self.pages.setWrapping(False)
        self.pages.setResizeMode(QListView.ResizeMode.Adjust)
        self.pages.setIconSize(QSize(110, 140))
        self.pages.setMinimumWidth(160)
        self.pages.setMaximumWidth(220)
        self.setWidget(self.pages)
        self._viewer: ViewerService | None = None
        self._rendered: set[int] = set()
        self.pages.currentRowChanged.connect(self._on_page_selected)
        self.pages.verticalScrollBar().valueChanged.connect(self._schedule_render)

    def set_document(self, viewer: ViewerService, count: int, current: int) -> None:
        self._viewer = viewer
        self._rendered.clear()
        with QSignalBlocker(self.pages):
            self.pages.clear()
            for index in range(count):
                item = QListWidgetItem(f"Page {index + 1}")
                item.setSizeHint(QSize(150, 165))
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
                self.pages.addItem(item)
        self.select_page(current)
        self._schedule_render()

    def select_page(self, index: int) -> None:
        if 0 <= index < self.pages.count():
            with QSignalBlocker(self.pages):
                self.pages.setCurrentRow(index)
            self._schedule_render()

    def _on_page_selected(self, index: int) -> None:
        if index >= 0:
            self.page_selected.emit(index)

    def _schedule_render(self, *_args) -> None:
        QTimer.singleShot(0, self._render_visible)

    def _render_visible(self) -> None:
        if self._viewer is None or not self.isVisible():
            return
        visible = self.pages.viewport().rect()
        start = self.pages.indexAt(QPoint(10, visible.top() + 5)).row()
        end = self.pages.indexAt(QPoint(10, visible.bottom() - 5)).row()
        if start < 0:
            start = 0
        if end < start:
            end = min(start + 5, self.pages.count() - 1)
        for index in range(start, min(end + 1, self.pages.count())):
            if index not in self._rendered:
                self._render_thumbnail(index)

    def _render_thumbnail(self, index: int) -> None:
        if self._viewer is None:
            return
        try:
            pixmap = self._viewer.render(index, 0.18)
            image = QImage(
                pixmap.samples, pixmap.width, pixmap.height,
                pixmap.stride, QImage.Format.Format_RGB888,
            ).copy()
        except (RuntimeError, ValueError):
            return
        self.pages.item(index).setIcon(QIcon(QPixmap.fromImage(image)))
        self._rendered.add(index)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._schedule_render()
