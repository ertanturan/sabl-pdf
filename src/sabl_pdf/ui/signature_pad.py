from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QVBoxLayout, QWidget


class SignatureSurface(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(450, 160)
        self.strokes: list[list[tuple[float, float]]] = []
        self.setAutoFillBackground(True)

    def set_strokes(self, strokes: list[list[tuple[float, float]]]) -> None:
        self.strokes = [list(stroke) for stroke in strokes]
        self.update()

    def clear(self) -> None:
        self.strokes.clear()
        self.update()

    def _point(self, position) -> tuple[float, float]:
        return (
            max(0.0, min(1.0, position.x() / max(1, self.width()))),
            max(0.0, min(1.0, position.y() / max(1, self.height()))),
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.strokes.append([self._point(event.position())])
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self.strokes and event.buttons() & Qt.MouseButton.LeftButton:
            self.strokes[-1].append(self._point(event.position()))
            self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("white"))
        painter.setPen(QPen(QColor("black"), 2.2))
        for stroke in self.strokes:
            for first, last in zip(stroke, stroke[1:]):
                painter.drawLine(
                    round(first[0] * self.width()), round(first[1] * self.height()),
                    round(last[0] * self.width()), round(last[1] * self.height()),
                )
        painter.end()


class SignatureDialog(QDialog):
    def __init__(
        self, parent=None, strokes: list[list[tuple[float, float]]] | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Draw signature")
        layout = QVBoxLayout(self)
        self.surface = SignatureSurface()
        self.surface.set_strokes(strokes or [])
        layout.addWidget(self.surface)
        clear = QPushButton("Clear", self)
        clear.clicked.connect(self.surface.clear)
        layout.addWidget(clear)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
