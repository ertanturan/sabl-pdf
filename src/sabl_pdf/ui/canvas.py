from collections.abc import Callable

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QMenu


class PdfCanvas(QGraphicsView):
    area_selected = Signal(int, tuple)
    page_changed = Signal(int)
    selection_cancelled = Signal()
    item_move_requested = Signal(int, int, tuple)
    item_delete_requested = Signal(int, int)
    copy_text_requested = Signal()
    redact_text_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._zoom = 1.0
        self._page_rects: list[QRectF] = []
        self._page_items: dict[int, object] = {}
        self._render_page: Callable | None = None
        self._text_selector: Callable | None = None
        self._text_selection = None
        self._text_drag_origin = None
        self._text_highlights: list = []
        self._selection_enabled = False
        self._click_size: tuple[float, float] | None = None
        self._origin = None
        self._origin_page: int | None = None
        self._rubber_band = None
        self._preview_item = None
        self._search_highlight = None
        self._placed_items: list[tuple[int, int, QRectF]] = []
        self._selected_item: tuple[int, int] | None = None
        self._item_outline = None
        self._drag_origin = None
        self._drag_rect = None
        self._dragging = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self._ignore_context_menu = False
        self.setBackgroundBrush(QBrush(QColor("#eaeaea")))
        self.verticalScrollBar().valueChanged.connect(self._viewport_changed)
        self.horizontalScrollBar().valueChanged.connect(self._viewport_changed)

    def display_pages(
        self, sizes: list[tuple[float, float]], render_page: Callable, zoom: float
    ) -> None:
        self._zoom = zoom
        self._render_page = render_page
        self._scene.clear()
        self._text_selection = None
        self._text_drag_origin = None
        self._text_highlights = []
        self._preview_item = None
        self._search_highlight = None
        self._item_outline = None
        self._selected_item = None
        self._placed_items = []
        self._drag_origin = None
        self._drag_rect = None
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
        preview_label: str | None = None,
        preview_image: str | None = None,
    ) -> None:
        self._remove_preview()
        if enabled:
            self.clear_text_selection()
        self._selection_enabled = enabled
        self._click_size = click_size if enabled else None
        self._origin = None
        self._origin_page = None
        self.setCursor(Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.ArrowCursor)
        if not enabled:
            return
        if click_size and preview_strokes:
            self._add_signature_preview(click_size, preview_strokes)
        elif click_size and preview_image:
            self._add_image_preview(click_size, preview_image)
        elif preview_label:
            self._add_label_preview(click_size or (90, 26), preview_label)

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
        self._preview_item = self._scene.addPath(path, QPen(QColor("#202020"), 1.4 * self._zoom))
        self._preview_item.setZValue(10)
        self._preview_item.hide()

    def _add_label_preview(self, size: tuple[float, float], label: str) -> None:
        width, height = size
        self._preview_item = self._scene.addRect(
            QRectF(0, 0, width * self._zoom, height * self._zoom),
            QPen(QColor("#2775cc"), 1.5, Qt.PenStyle.DashLine),
            QBrush(QColor(255, 255, 255, 175)),
        )
        caption = QGraphicsSimpleTextItem(label, self._preview_item)
        caption.setBrush(QBrush(QColor("#202020")))
        caption.setPos(3, 2)
        self._preview_item.setZValue(10)
        self._preview_item.setOpacity(0.75)
        self._preview_item.hide()

    def _add_image_preview(self, size: tuple[float, float], image: str) -> None:
        width, height = size
        pixmap = QPixmap(image).scaled(
            max(1, round(width * self._zoom)),
            max(1, round(height * self._zoom)),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if pixmap.isNull():
            self._add_label_preview(size, "Signature")
            return
        self._preview_item = self._scene.addPixmap(pixmap)
        self._preview_item.setOpacity(0.7)
        self._preview_item.setZValue(10)
        self._preview_item.hide()

    def _placement_anchor(self, page: int, position):
        if self._click_size is None:
            return position
        bounds = self._page_rects[page]
        width = self._click_size[0] * self._zoom
        height = self._click_size[1] * self._zoom
        x = max(bounds.left(), min(position.x(), bounds.right() - width))
        y = max(bounds.top(), min(position.y(), bounds.bottom() - height))
        return type(position)(x, y)

    def _move_preview(self, position) -> None:
        if self._preview_item is None:
            return
        page = self._page_at(position)
        self._preview_item.setVisible(page is not None and self._origin is None)
        if page is not None:
            self._preview_item.setPos(self._placement_anchor(page, position))

    def leaveEvent(self, event) -> None:
        if self._preview_item is not None:
            self._preview_item.hide()
        super().leaveEvent(event)

    def set_text_selector(self, selector: Callable | None) -> None:
        self._text_selector = selector

    def selected_text(self) -> str:
        return self._text_selection.text if self._text_selection is not None else ""

    def selected_text_regions(self):
        return self._text_selection

    def clear_text_selection(self) -> None:
        for item in self._text_highlights:
            self._scene.removeItem(item)
        self._text_highlights = []
        self._text_selection = None

    def _update_text_selection(self, scene_position) -> None:
        if self._text_drag_origin is None or self._text_selector is None:
            return
        page, start = self._text_drag_origin
        bounds = self._page_rects[page]
        end_x = max(bounds.left(), min(scene_position.x(), bounds.right()))
        end_y = max(bounds.top(), min(scene_position.y(), bounds.bottom()))
        origin = ((start.x() - bounds.left()) / self._zoom,
                  (start.y() - bounds.top()) / self._zoom)
        destination = ((end_x - bounds.left()) / self._zoom,
                       (end_y - bounds.top()) / self._zoom)
        selection = self._text_selector(page, origin, destination)
        self.clear_text_selection()
        if selection is None:
            return
        self._text_selection = selection
        for x0, y0, x1, y1 in selection.display_rects:
            item = self._scene.addRect(
                QRectF(bounds.left() + x0 * self._zoom,
                       bounds.top() + y0 * self._zoom,
                       (x1 - x0) * self._zoom, (y1 - y0) * self._zoom),
                QPen(Qt.PenStyle.NoPen), QBrush(QColor(39, 117, 204, 95)),
            )
            item.setZValue(15)
            self._text_highlights.append(item)

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

    def set_placed_items(self, items: list[tuple[int, int, tuple]]) -> None:
        self.clear_item_selection()
        self._placed_items = []
        for page, xref, bounds in items:
            if not 0 <= page < len(self._page_rects):
                continue
            page_rect = self._page_rects[page]
            x0, y0, x1, y1 = bounds
            rect = QRectF(
                page_rect.left() + x0 * self._zoom,
                page_rect.top() + y0 * self._zoom,
                (x1 - x0) * self._zoom,
                (y1 - y0) * self._zoom,
            )
            self._placed_items.append((page, xref, rect))

    def _item_at(self, position) -> tuple[int, int, QRectF] | None:
        for item in reversed(self._placed_items):
            if item[2].contains(position):
                return item
        return None

    def _select_item(self, item: tuple[int, int, QRectF] | None) -> None:
        self.clear_item_selection()
        if item is None:
            return
        page, xref, rect = item
        self._selected_item = (page, xref)
        self._item_outline = self._scene.addRect(
            rect,
            QPen(QColor("#2775cc"), 2, Qt.PenStyle.DashLine),
            QBrush(QColor(39, 117, 204, 35)),
        )
        self._item_outline.setZValue(20)
        self.setFocus()

    def clear_item_selection(self) -> None:
        if self._item_outline is not None:
            self._scene.removeItem(self._item_outline)
            self._item_outline = None
        self._selected_item = None
        self._drag_origin = None
        self._drag_rect = None
        self._dragging = False

    def _drag_item(self, position) -> None:
        if self._selected_item is None or self._drag_rect is None:
            return
        page = self._selected_item[0]
        page_rect = self._page_rects[page]
        delta = position - self._drag_origin
        dx = max(page_rect.left() - self._drag_rect.left(),
                 min(delta.x(), page_rect.right() - self._drag_rect.right()))
        dy = max(page_rect.top() - self._drag_rect.top(),
                 min(delta.y(), page_rect.bottom() - self._drag_rect.bottom()))
        self._dragging = abs(dx) > 2 or abs(dy) > 2
        self._item_outline.setRect(self._drag_rect.translated(dx, dy))

    def _finish_item_drag(self) -> None:
        key = self._selected_item
        if key is None or not self._dragging:
            return
        page, xref = key
        page_rect = self._page_rects[page]
        rect = self._item_outline.rect()
        self.item_move_requested.emit(page, xref, (
            (rect.left() - page_rect.left()) / self._zoom,
            (rect.top() - page_rect.top()) / self._zoom,
            (rect.right() - page_rect.left()) / self._zoom,
            (rect.bottom() - page_rect.top()) / self._zoom,
        ))

    def delete_selected_item(self) -> None:
        if self._selected_item is not None:
            self.item_delete_requested.emit(*self._selected_item)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected_item()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self._text_selection is not None:
            self.clear_text_selection()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self._selected_item is not None:
            self.clear_item_selection()
            event.accept()
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event) -> None:
        if self._ignore_context_menu:
            self._ignore_context_menu = False
            event.accept()
            return
        if self._selection_enabled:
            event.accept()
            return
        item = self._item_at(self.mapToScene(event.pos()))
        if item is None and self._text_selection is not None:
            menu = QMenu(self)
            menu.addAction("Copy selected text", self.copy_text_requested.emit)
            menu.exec(event.globalPos())
            return
        if item is None:
            super().contextMenuEvent(event)
            return
        self._select_item(item)
        menu = QMenu(self)
        menu.addAction("Delete selected item", self.delete_selected_item)
        menu.exec(event.globalPos())

    def mousePressEvent(self, event) -> None:
        if self._selection_enabled and event.button() == Qt.MouseButton.RightButton:
            self._ignore_context_menu = True
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
        if not self._selection_enabled and event.button() == Qt.MouseButton.LeftButton:
            position = self.mapToScene(event.position().toPoint())
            item = self._item_at(position)
            self._select_item(item)
            self.clear_text_selection()
            if item is not None:
                self._drag_origin = position
                self._drag_rect = QRectF(item[2])
                event.accept()
                return
            page = self._page_at(position)
            if page is not None and self._text_selector is not None:
                self._text_drag_origin = (page, position)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._text_drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._update_text_selection(self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._drag_item(self.mapToScene(event.position().toPoint()))
            event.accept()
            return
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
        if event.button() == Qt.MouseButton.LeftButton and self._text_drag_origin is not None:
            self._update_text_selection(self.mapToScene(event.position().toPoint()))
            self._text_drag_origin = None
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._drag_origin is not None:
            self._drag_item(self.mapToScene(event.position().toPoint()))
            self._finish_item_drag()
            self._drag_origin = None
            self._drag_rect = None
            self._dragging = False
            event.accept()
            return
        if self._selection_enabled and self._origin is not None and self._origin_page is not None:
            page_index = self._origin_page
            page_rect = self._page_rects[page_index]
            end = self.mapToScene(event.position().toPoint())
            rect = QRectF(self._origin, end).normalized().intersected(page_rect)
            if rect.width() < 2 and rect.height() < 2 and self._click_size is not None:
                width, height = self._click_size
                anchor = self._placement_anchor(page_index, end)
                rect = QRectF(
                    anchor.x(), anchor.y(), width * self._zoom, height * self._zoom
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
