from collections.abc import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QStyle, QToolBar, QVBoxLayout, QWidget

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.viewer import SearchMatch, ViewerService
from sabl_pdf.ui.canvas import PdfCanvas
from sabl_pdf.ui.search_bar import SearchBar
from sabl_pdf.ui.viewer_actions import ViewerActions
from sabl_pdf.services.text_boxes import TextBoxService
from sabl_pdf.ui.text_actions import TextActions
from sabl_pdf.services.forms import FormService
from sabl_pdf.services.signatures import SignatureService
from sabl_pdf.ui.signature_actions import SignatureActions
from sabl_pdf.services.pages import PageService
from sabl_pdf.ui.page_actions import PageActions
from sabl_pdf.services.annotations import AnnotationService
from sabl_pdf.ui.annotation_actions import AnnotationActions
from sabl_pdf.services.compression import CompressionService
from sabl_pdf.ui.compression_actions import CompressionActions
from sabl_pdf.services.conversion import ConversionService
from sabl_pdf.ui.conversion_actions import ConversionActions
from sabl_pdf.services.ocr import OcrService
from sabl_pdf.ui.ocr_actions import OcrActions


class MainWindow(ViewerActions, TextActions, SignatureActions, PageActions, AnnotationActions, CompressionActions, ConversionActions, OcrActions, QMainWindow):

    def __init__(self, session: DocumentSession | None = None) -> None:
        super().__init__()
        self.session = session or DocumentSession()
        self.viewer = ViewerService(self.session)
        self.text_boxes = TextBoxService(self.session)
        self.forms = FormService(self.session)
        self.signatures = SignatureService(self.session)
        self.pages = PageService(self.session)
        self.annotations = AnnotationService(self.session)
        self.compression = CompressionService(self.session)
        self.conversion = ConversionService(self.session)
        self.ocr = OcrService(self.session)
        self.page_index = 0
        self.zoom = 1.0
        self._selection_action: Callable[[tuple], None] | None = None
        self.setWindowTitle("SABL PDF")
        self.resize(1024, 780)
        self.canvas = PdfCanvas()
        self.canvas.area_selected.connect(self._on_area_selected)
        self.canvas.page_changed.connect(self._on_page_changed)
        self.canvas.selection_cancelled.connect(self._on_selection_cancelled)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        self.search_bar = SearchBar(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.canvas)
        self.setCentralWidget(central)
        self._search_matches: list[SearchMatch] = []
        self._search_index = -1
        self.search_bar.search_requested.connect(self._search_query)
        self.search_bar.next_requested.connect(lambda: self._move_search(1))
        self.search_bar.previous_requested.connect(lambda: self._move_search(-1))
        self.search_bar.close_requested.connect(self._close_search)
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
        edit = self.menuBar().addMenu("Text & Forms")
        self._action(edit, "Add text box", self.add_text_box)
        self._action(edit, "Edit text box", self.edit_text_box)
        self._action(edit, "Remove text box", self.remove_text_box)
        self._action(edit, "Fill form field", self.fill_form)
        signatures = self.menuBar().addMenu("Signatures")
        self._action(signatures, "Import signature image", self.import_signature)
        self._action(signatures, "Draw signature", self.draw_signature)
        self._action(signatures, "Use saved signature", self.use_saved_signature)
        pages = self.menuBar().addMenu("Pages")
        self._action(pages, "Merge PDF", self.merge_pdf)
        self._action(pages, "Split page range", self.split_pdf)
        self._action(pages, "Delete page", self.delete_page)
        self._action(pages, "Rotate page", self.rotate_page)
        self._action(pages, "Move page earlier", lambda: self.move_page(-1))
        self._action(pages, "Move page later", lambda: self.move_page(1))
        annotations = self.menuBar().addMenu("Annotations")
        self._action(annotations, "Highlight selection", lambda: self.mark_selection("highlight"))
        self._action(annotations, "Underline selection", lambda: self.mark_selection("underline"))
        self._action(annotations, "Add note", self.add_note)
        self._action(annotations, "Remove annotation", self.remove_annotation)
        tools = self.menuBar().addMenu("Tools")
        self._action(tools, "Compress to file", self.compress_pdf)
        self._action(tools, "Add images as pages", self.add_images)
        self._action(tools, "Export pages as images", self.export_images)
        self._action(tools, "OCR current page", self.ocr_page)
        self._action(tools, "Export OCR text", self.export_ocr)


    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Quick access", self)
        toolbar.setObjectName("quick_access")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        self.quick_actions: dict[str, QAction] = {}
        self._toolbar_button(toolbar, "open", "Open", self.open_pdf, "SP_DialogOpenButton")
        self._toolbar_button(toolbar, "save", "Save", self.save_pdf, "SP_DialogSaveButton")
        self._toolbar_button(
            toolbar, "find", "Find", self.search_text, "SP_FileDialogContentsView", "Ctrl+F"
        )
        toolbar.addSeparator()
        self._toolbar_button(toolbar, "text", "Add Text", self.add_text_box, "SP_FileIcon")
        self._toolbar_button(
            toolbar, "highlight", "Highlight",
            lambda: self.mark_selection("highlight"), "SP_DialogApplyButton",
        )
        self._toolbar_button(toolbar, "sign", "Sign", self.draw_signature, "SP_FileDialogInfoView")
        toolbar.addSeparator()
        self._toolbar_button(toolbar, "rotate", "Rotate", self.rotate_page, "SP_BrowserReload")
        self._toolbar_button(
            toolbar, "compress", "Compress", self.compress_pdf, "SP_DriveHDIcon"
        )
        self._build_navigation_toolbar()

    def _toolbar_button(
        self, toolbar: QToolBar, key: str, text: str, handler: Callable,
        icon: str, shortcut: str | None = None,
    ) -> None:
        action = QAction(self.style().standardIcon(getattr(QStyle.StandardPixmap, icon)), text, self)
        action.setObjectName(f"quick_{key}")
        action.setToolTip(text + (f" ({shortcut})" if shortcut else ""))
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(handler)
        toolbar.addAction(action)
        self.quick_actions[key] = action

    def _build_navigation_toolbar(self) -> None:
        navigation = QToolBar("Page navigation", self)
        navigation.setObjectName("page_navigation")
        navigation.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, navigation)
        for text, handler in [
            ("Previous", lambda: self.change_page(-1)),
            ("Next", lambda: self.change_page(1)),
            ("Zoom Out", lambda: self.change_zoom(0.8)),
            ("Zoom In", lambda: self.change_zoom(1.25)),
        ]:
            action = QAction(text, self)
            action.triggered.connect(handler)
            navigation.addAction(action)


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
            self.canvas.display_pages([], self.viewer.render, self.zoom)
            return
        requested_page = min(max(0, self.page_index), len(document) - 1)
        self.canvas.display_pages(
            self.viewer.page_sizes(),
            lambda index: self.viewer.render(index, self.zoom),
            self.zoom,
        )
        self.page_index = requested_page
        self.canvas.scroll_to_page(requested_page)
        self._update_page_status()
        self.setWindowTitle(f"SABL PDF | {self.session.path.name if self.session.path else 'Unsaved'}")

    def _update_page_status(self) -> None:
        self.status.setText(
            f"Page {self.page_index + 1} / {self.viewer.page_count()} | {round(self.zoom * 100)}%"
        )

    def _on_page_changed(self, page_index: int) -> None:
        self.page_index = page_index
        self._update_page_status()


    def _after_edit(self) -> None:
        self._refresh()
        if self.search_bar.query():
            self._search_query(self.search_bar.query())


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


    def _select_area(
        self,
        callback: Callable[[tuple], None],
        click_size: tuple[float, float] | None = None,
        preview_strokes: list[list[tuple[float, float]]] | None = None,
    ) -> None:
        if not self._require_document():
            return
        self._selection_action = callback
        self.canvas.set_selection_enabled(True, click_size, preview_strokes)
        self.status.setText(
            "Click to place or drag to size; right-click to cancel"
            if click_size else "Drag a rectangle on the page; right-click to cancel"
        )

    def _on_selection_cancelled(self) -> None:
        self._selection_action = None
        self._update_page_status()


    def _on_area_selected(self, page_index: int, rect: tuple) -> None:
        self.page_index = page_index
        action = self._selection_action
        self._selection_action = None
        if action is not None:
            self._run(lambda: action(rect))
