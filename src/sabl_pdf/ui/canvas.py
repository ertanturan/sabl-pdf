from collections.abc import Callable

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


class PdfCanvas(QGraphicsView):
    area_selected = Signal(int, tuple)
    page_changed = Signal(int)
    selection_cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._zoom = 1.0
        self._page_rects: list[QRectF] = []
        self._page_items: dict[int, object] = {}
        self._render_page: Callable | None = None
        self._selection_enabled = False
        self._click_size: tuple[float, float] | None = None
        self._origin = None
        self._origin_page: int | None = None
        self._rubber_band = None
        self._preview_item = None
        self._search_highlight = None
        self.setBackgroundBrush(QBrush(QColor("#eaeaea")))
        self.verticalScrollBar().valueChanged.connect(self._viewport_changed)
        self.horizontalScrollBar().valueChanged.connect(self._viewport_changed)

    def display_pages(
        self, sizes: list[tuple[float, float]], render_page: Callable, zoom: float
    ) -> None:
        self._zoom = zoom
        self._render_page = render_page
        self._scene.clear()
        self._preview_item = None
        self._search_highlight = None
        self._page_items.clear()
        self._page_rects = self._layout_pages(sizes)
        width = max((rect.right() for rect in self._page_rects), default=0)
        height = self._page_rects[-1].bottom() + 16 if self._page_rects else 0
        self._scene.setSceneRect(QRectF(0, 0, width + 16, height))
        self._viewport_changed()

    def _layout_pages(self, sizes: list[tuple[float, float]]) -> list[QRectF]:
        width = max((size[0] * self._zoom for size in sizes), default=0)
        y = 16.0
        result = []
        for page_width, page_height in sizes:
            scaled_width = page_width * self._zoom
            scaled_height = page_height * self._zoom
            result.append(QRectF(16 + (width - scaled_width) / 2, y, scaled_width, scaled_height))
            y += scaled_height + 16
        return result

    def _viewport_changed(self, *args) -> None:
        if not self._page_rects:
            return
        self._load_visible_pages()
        self._notify_page_changed()

    def _load_visible_pages(self) -> None:
        visible = self.mapToScene(self.viewport().rect()).boundingRect()
        nearby = visible.adjusted(0, -visible.height(), 0, visible.height())
        for index, rect in enumerate(self._page_rects):
            if not rect.intersects(nearby):
                item = self._page_items.pop(index, None)
                if item is not None:
                    self._scene.removeItem(item)
            elif index not in self._page_items:
                self._load_page(index, rect)

    def _load_page(self, index: int, rect: QRectF) -> None:
        if self._render_page is None:
            return
        try:
            pixmap = self._render_page(index)
        except (RuntimeError, ValueError):
            item = self._scene.addText(
                f"Page {index + 1} could not be displayed. The PDF may be damaged."
            )
        else:
            image = QImage(
                pixmap.samples, pixmap.width, pixmap.height,
                pixmap.stride, QImage.Format.Format_RGB888,
            ).copy()
            item = self._scene.addPixmap(QPixmap.fromImage(image))
        item.setPos(rect.topLeft())
        self._page_items[index] = item

    def _notify_page_changed(self) -> None:
        center = self.mapToScene(self.viewport().rect().center())
        for index, rect in enumerate(self._page_rects):
            if center.y() < rect.bottom():
                self.page_changed.emit(index)
                return
        self.page_changed.emit(len(self._page_rects) - 1)

    def scroll_to_page(self, index: int) -> None:
        if not 0 <= index < len(self._page_rects):
            return
        rect = self._page_rects[index]
        self.centerOn(rect.center().x(), rect.top() + self.viewport().height() / 2)
        self._viewport_changed()

    def set_selection_enabled(
        self,
        enabled: bool,
        click_size: tuple[float, float] | None = None,
        preview_strokes: list[list[tuple[float, float]]] | None = None,
    ) -> None:
        self._remove_preview()
        self._selection_enabled = enabled
        self._click_size = click_size if enabled else None
        self._origin = None
        self._origin_page = None
        self.setCursor(Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.ArrowCursor)
        if enabled and click_size and preview_strokes:
            self._add_signature_preview(click_size, preview_strokes)

    def _remove_preview(self) -> None:
        if self._preview_item is not None:
            self._scene.removeItem(self._preview_item)
            self._preview_item = None

    def _add_signature_preview(
        self, size: tuple[float, float], strokes: list[list[tuple[float, float]]]
    ) -> None:
        path = QPainterPath()
        width, height = size
        for stroke in strokes:
            if not stroke:
                continue
            path.moveTo(stroke[0][0] * width * self._zoom, stroke[0][1] * height * self._zoom)
            for x, y in stroke[1:]:
                path.lineTo(x * width * self._zoom, y * height * self._zoom)
        self._preview_item = self._scene.addPath(path, QPen(QColor("#2775cc"), 2))
        self._preview_item.setZValue(10)
        self._preview_item.hide()

    def _move_preview(self, position) -> None:
        if self._preview_item is None:
            return
        page = self._page_at(position)
        self._preview_item.setVisible(page is not None)
        if page is not None:
            self._preview_item.setPos(position)

    def clear_search_highlight(self) -> None:
        if self._search_highlight is not None:
            self._scene.removeItem(self._search_highlight)
            self._search_highlight = None

    def highlight(self, bounds: tuple[float, float, float, float], page: int) -> None:
        self.clear_search_highlight()
        x0, y0, x1, y1 = bounds
        origin = self._page_rects[page].topLeft()
        self._search_highlight = self._scene.addRect(
            QRectF(origin.x() + x0 * self._zoom, origin.y() + y0 * self._zoom,
                   (x1 - x0) * self._zoom, (y1 - y0) * self._zoom),
            QPen(QColor("#e6aa00"), 2), QBrush(QColor(255, 210, 0, 70)),
        )

    def _page_at(self, position) -> int | None:
        for index, rect in enumerate(self._page_rects):
            if rect.contains(position):
                return index
        return None

    def mousePressEvent(self, event) -> None:
        if self._selection_enabled and event.button() == Qt.MouseButton.RightButton:
            self._cancel_selection()
            event.accept()
            return
        if self._selection_enabled and event.button() == Qt.MouseButton.LeftButton:
            position = self.mapToScene(event.position().toPoint())
            page = self._page_at(position)
            if page is not None:
                self._origin = position
                self._origin_page = page
                self._rubber_band = self._scene.addRect(
                    QRectF(position, position), QPen(QColor("#2775cc"), 2),
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._selection_enabled:
            self._move_preview(self.mapToScene(event.position().toPoint()))
        if self._selection_enabled and self._origin is not None:
            position = self.mapToScene(event.position().toPoint())
            self._rubber_band.setRect(QRectF(self._origin, position).normalized())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def cancel_selection(self) -> None:
        if self._selection_enabled:
            self._cancel_selection()

    def _cancel_selection(self) -> None:
        if self._rubber_band is not None:
            self._scene.removeItem(self._rubber_band)
            self._rubber_band = None
        self.set_selection_enabled(False)
        self.selection_cancelled.emit()

    def mouseReleaseEvent(self, event) -> None:
        if self._selection_enabled and self._origin is not None and self._origin_page is not None:
            page_index = self._origin_page
            page_rect = self._page_rects[page_index]
            end = self.mapToScene(event.position().toPoint())
            rect = QRectF(self._origin, end).normalized().intersected(page_rect)
            if rect.width() < 2 and rect.height() < 2 and self._click_size is not None:
                width, height = self._click_size
                rect = QRectF(
                    end.x(), end.y(), width * self._zoom, height * self._zoom
                ).intersected(page_rect)
            if self._rubber_band is not None:
                self._scene.removeItem(self._rubber_band)
                self._rubber_band = None
            self.set_selection_enabled(False)
            if rect.width() >= 2 and rect.height() >= 2:
                self.area_selected.emit(page_index, (
                    (rect.left() - page_rect.left()) / self._zoom,
                    (rect.top() - page_rect.top()) / self._zoom,
                    (rect.right() - page_rect.left()) / self._zoom,
                    (rect.bottom() - page_rect.top()) / self._zoom,
                ))
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._viewport_changed()
