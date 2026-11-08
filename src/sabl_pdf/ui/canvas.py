from PySide6.QtCore import QRectF, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


class PdfCanvas(QGraphicsView):
    area_selected = Signal(tuple)

    def __init__(self) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._zoom = 1.0
        self._selection_enabled = False
        self._origin = None
        self._rubber_band = None
        self.setBackgroundBrush(QBrush(QColor("#eaeaea")))

    def display(self, pixmap, zoom: float) -> None:
        self._zoom = zoom
        image = QImage(
            pixmap.samples, pixmap.width, pixmap.height,
            pixmap.stride, QImage.Format.Format_RGB888,
        ).copy()
        self._scene.clear()
        self._scene.addPixmap(QPixmap.fromImage(image))
        self._scene.setSceneRect(QRectF(0, 0, pixmap.width, pixmap.height))

    def set_selection_enabled(self, enabled: bool) -> None:
        self._selection_enabled = enabled
        self._origin = None

    def highlight(self, bounds: tuple[float, float, float, float]) -> None:
        x0, y0, x1, y1 = bounds
        self._scene.addRect(
            QRectF(x0 * self._zoom, y0 * self._zoom,
                   (x1 - x0) * self._zoom, (y1 - y0) * self._zoom),
            QPen(QColor("#e6aa00"), 2), QBrush(QColor(255, 210, 0, 70)),
        )

    def mousePressEvent(self, event) -> None:
        if self._selection_enabled:
            self._origin = self.mapToScene(event.position().toPoint())
            self._rubber_band = self._scene.addRect(
                QRectF(self._origin, self._origin), QPen(QColor("#2775cc"), 2),
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._selection_enabled and self._origin is not None:
            position = self.mapToScene(event.position().toPoint())
            self._rubber_band.setRect(QRectF(self._origin, position).normalized())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._selection_enabled and self._origin is not None:
            end = self.mapToScene(event.position().toPoint())
            rect = QRectF(self._origin, end).normalized().intersected(self._scene.sceneRect())
            if self._rubber_band is not None:
                self._scene.removeItem(self._rubber_band)
                self._rubber_band = None
            self._origin = None
            self._selection_enabled = False
            if rect.width() >= 2 and rect.height() >= 2:
                self.area_selected.emit((
                    rect.left() / self._zoom, rect.top() / self._zoom,
                    rect.right() / self._zoom, rect.bottom() / self._zoom,
                ))
            event.accept()
            return
        super().mouseReleaseEvent(event)
