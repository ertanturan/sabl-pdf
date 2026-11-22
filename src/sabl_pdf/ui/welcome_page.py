from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class WelcomePage(QWidget):
    open_requested = Signal()
    default_app_requested = Signal()
    file_dropped = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("welcome_page")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)
        heading = QLabel("Open a PDF to get started", self)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet("font-size: 24px; font-weight: 600;")
        instruction = QLabel("Open a file or drag a PDF onto this window", self)
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet("color: #687385; font-size: 14px;")
        button = QPushButton("Open PDF", self)
        button.setObjectName("welcome_open")
        button.setMinimumSize(180, 44)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda _checked=False: self.open_requested.emit())
        layout.addWidget(heading)
        layout.addWidget(instruction)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)
        default_button = QPushButton("Set as default PDF app", self)
        default_button.setObjectName("welcome_default_pdf")
        default_button.setMinimumWidth(180)
        default_button.setCursor(Qt.CursorShape.PointingHandCursor)
        default_button.setToolTip("Choose SABL PDF for .pdf files in Windows Settings")
        default_button.clicked.connect(lambda _checked=False: self.default_app_requested.emit())
        layout.addWidget(default_button, alignment=Qt.AlignmentFlag.AlignHCenter)


    def _pdf_path(self, event) -> str | None:
        if not event.mimeData().hasUrls():
            return None
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local and Path(local).suffix.lower() == ".pdf":
                return local
        return None

    def dragEnterEvent(self, event) -> None:
        if self._pdf_path(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        path = self._pdf_path(event)
        if path:
            self.file_dropped.emit(path)
            event.acceptProposedAction()
        else:
            event.ignore()
