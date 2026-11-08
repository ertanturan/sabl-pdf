from PySide6.QtCore import QSignalBlocker, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QToolButton, QWidget


class SearchBar(QWidget):
    search_requested = Signal(str)
    next_requested = Signal()
    previous_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("search_bar")
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Find in document")
        self.search_input.setClearButtonEnabled(True)
        self.results = QLabel("Find in PDF", self)
        self.results.setMinimumWidth(100)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._emit_search)
        self.search_input.textChanged.connect(self._schedule_search)
        self.search_input.returnPressed.connect(self._emit_search)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.results)
        self._button(layout, "‹", "Previous match", self.previous_requested.emit)
        self._button(layout, "›", "Next match", self.next_requested.emit)
        self._button(layout, "×", "Close find", self.close_requested.emit)
        self.hide()

    def _button(self, layout: QHBoxLayout, text: str, tooltip: str, callback) -> None:
        button = QToolButton(self)
        button.setText(text)
        button.setToolTip(tooltip)
        button.setObjectName(f"search_{tooltip.split()[0].lower()}")
        button.clicked.connect(lambda _checked=False: callback())
        layout.addWidget(button)

    def _schedule_search(self, _text: str) -> None:
        self._timer.start()

    def _emit_search(self) -> None:
        self._timer.stop()
        self.search_requested.emit(self.search_input.text())

    def focus_query(self) -> None:
        self.show()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def dismiss(self) -> None:
        self._timer.stop()
        self.hide()

    def set_position(self, index: int, count: int) -> None:
        self.results.setText(f"{index + 1} of {count}" if count else "No matches")

    def set_query(self, query: str) -> None:
        self._timer.stop()
        with QSignalBlocker(self.search_input):
            self.search_input.setText(query)

    def query(self) -> str:
        return self.search_input.text()
