from collections.abc import Callable

from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QToolBar, QVBoxLayout, QWidget

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.viewer import ViewerService
from sabl_pdf.ui.canvas import PdfCanvas
from sabl_pdf.ui.viewer_actions import ViewerActions


class MainWindow(ViewerActions, QMainWindow):

    def __init__(self, session: DocumentSession | None = None) -> None:
        super().__init__()
        self.session = session or DocumentSession()
        self.viewer = ViewerService(self.session)
        self.page_index = 0
        self.zoom = 1.0
        self._selection_action: Callable[[tuple], None] | None = None
        self.setWindowTitle("SABL PDF")
        self.resize(1024, 780)
        self.canvas = PdfCanvas()
        self.canvas.area_selected.connect(self._on_area_selected)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.canvas)
        self.setCentralWidget(central)
        self.status = QLabel("Open a PDF to begin")
        self.statusBar().addPermanentWidget(self.status)
        self._build_menu()
        self._build_toolbar()


    def _action(self, menu, text: str, handler, shortcut: str | None = None) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(handler)
        menu.addAction(action)
        return action


    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        self._action(file_menu, "Open PDF", self.open_pdf, "Ctrl+O")
        self._action(file_menu, "Save", self.save_pdf, "Ctrl+S")
        self._action(file_menu, "Save as", self.save_as)
        self._action(file_menu, "Copy page text", self.copy_page_text, "Ctrl+C")
        self._action(file_menu, "Copy selected text", self.copy_selection)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Navigation", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for text, handler in [
            ("Open", self.open_pdf), ("Save", self.save_pdf),
            ("Previous", lambda: self.change_page(-1)),
            ("Next", lambda: self.change_page(1)),
            ("Zoom -", lambda: self.change_zoom(0.8)),
            ("Zoom +", lambda: self.change_zoom(1.25)),
            ("Search", self.search_text),
        ]:
            action = QAction(text, self)
            action.triggered.connect(handler)
            toolbar.addAction(action)


    def _require_document(self) -> bool:
        try:
            self.session.document
            return True
        except RuntimeError:
            QMessageBox.information(self, "No document", "Open a PDF first.")
            return False


    def _run(self, operation: Callable[[], None]) -> None:
        try:
            operation()
        except Exception as exc:
            QMessageBox.warning(self, "SABL PDF", str(exc))


    def _refresh(self) -> None:
        document = self.session.document
        if len(document) == 0:
            self.status.setText("No pages")
            self.canvas.scene().clear()
            return
        self.page_index = min(max(0, self.page_index), len(document) - 1)
        self.canvas.display(self.viewer.render(self.page_index, self.zoom), self.zoom)
        self.status.setText(f"Page {self.page_index + 1} / {len(document)} | {round(self.zoom * 100)}%")
        self.setWindowTitle(f"SABL PDF | {self.session.path.name if self.session.path else 'Unsaved'}")


    def _after_edit(self) -> None:
        self._refresh()


    def _confirm_changes(self) -> bool:
        if not self.session.dirty:
            return True
        decision = QMessageBox.question(
            self, "Unsaved changes", "Discard unsaved changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return decision == QMessageBox.StandardButton.Yes


    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._confirm_changes():
            event.ignore()
            return
        self.session.close()
        event.accept()


    def _select_area(self, callback: Callable[[tuple], None]) -> None:
        if not self._require_document():
            return
        self._selection_action = callback
        self.canvas.set_selection_enabled(True)
        self.status.setText("Drag a rectangle on the page")


    def _on_area_selected(self, rect: tuple) -> None:
        action = self._selection_action
        self._selection_action = None
        if action is not None:
            self._run(lambda: action(rect))
