from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QStackedWidget, QStyle, QTabWidget, QToolBar, QVBoxLayout, QWidget

from sabl_pdf import __version__
from sabl_pdf.services.release_notes import installed_release_notes
from sabl_pdf.ui.whats_new_dialog import WhatsNewDialog
from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.viewer import SearchMatch, ViewerService
from sabl_pdf.ui.canvas import PdfCanvas
from sabl_pdf.ui.document_tab import DocumentTab
from sabl_pdf.ui.search_bar import SearchBar
from sabl_pdf.ui.welcome_page import WelcomePage
from sabl_pdf.ui.page_thumbnails import PageThumbnails
from sabl_pdf.ui.viewer_actions import ViewerActions
from sabl_pdf.services.placed_items import PlacedItemService
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
from sabl_pdf.services.redaction import RedactionService
from sabl_pdf.ui.redaction_actions import RedactionActions


class MainWindow(ViewerActions, TextActions, SignatureActions, PageActions, AnnotationActions, CompressionActions, ConversionActions, OcrActions, RedactionActions, QMainWindow):

    def __init__(
        self, session: DocumentSession | None = None, settings: QSettings | None = None
    ) -> None:
        super().__init__()
        self._ui_settings = settings or QSettings("SABL", "SABL PDF")
        self._initial_session = session
        self._active_tab: DocumentTab | None = None
        self._empty_session = session or DocumentSession()
        self.session = self._empty_session
        self.viewer = ViewerService(self.session)
        self.text_boxes = TextBoxService(self.session)
        self.placed_items = PlacedItemService(self.session)
        self.forms = FormService(self.session)
        self.signatures = SignatureService(self.session)
        self.pages = PageService(self.session)
        self.annotations = AnnotationService(self.session)
        self.compression = CompressionService(self.session)
        self.conversion = ConversionService(self.session)
        self.ocr = OcrService(self.session)
        self.redaction = RedactionService(self.session)
        self.page_index = 0
        self.zoom = 1.0
        self._selection_action: Callable[[tuple], None] | None = None
        self._active_tool: str | None = None
        self._document_actions: list[QAction] = []
        self.setWindowTitle("SABL PDF")
        self.resize(1024, 780)
        self._empty_canvas = PdfCanvas()
        self.canvas = self._empty_canvas
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        self.search_bar = SearchBar(self)
        layout.addWidget(self.search_bar)
        self.workspace = QStackedWidget(self)
        self.welcome = WelcomePage(self)
        self.workspace.addWidget(self.welcome)
        self.document_tabs = QTabWidget(self)
        self.document_tabs.setObjectName("document_tabs")
        self.document_tabs.setTabsClosable(True)
        self.document_tabs.setMovable(True)
        self.document_tabs.setDocumentMode(True)
        self.document_tabs.tabBar().setExpanding(False)
        self.document_tabs.currentChanged.connect(self._activate_document)
        self.document_tabs.tabCloseRequested.connect(self._close_document_tab)
        self.workspace.addWidget(self.document_tabs)
        layout.addWidget(self.workspace)
        self.setCentralWidget(central)
        self.welcome.open_requested.connect(self.open_pdf)
        self.welcome.file_dropped.connect(self.open_path)
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
        self._build_thumbnails()
        self._build_toolbar_preferences()
        self._build_cancel_shortcut()
        self._set_document_actions_enabled(False)


    def _action(self, menu, text: str, handler, shortcut: str | None = None) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(handler)
        menu.addAction(action)
        if text != "Open PDF":
            self._document_actions.append(action)
        return action


    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        self._action(file_menu, "Open PDF", self.open_pdf, "Ctrl+O")
        self._action(file_menu, "Close tab", self._close_current_tab, "Ctrl+W")
        self._action(file_menu, "Save", self.save_pdf, "Ctrl+S")
        self._action(file_menu, "Save as", self.save_as)
        self._action(file_menu, "Copy page text", self.copy_page_text)
        self._action(file_menu, "Copy selected text", self.copy_selection, "Ctrl+C")
        edit = self.menuBar().addMenu("Text & Forms")
        self._action(edit, "Add text box", self.add_text_box)
        self._action(edit, "Edit text box", self.edit_text_box)
        self._action(edit, "Remove text box", self.remove_text_box)
        self._action(edit, "Delete selected item", lambda: self.canvas.delete_selected_item(), "Delete")
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
        self._action(tools, "Redact information", self.redact_information)
        self._action(tools, "Redact an area", self.redact_area)
        help_menu = self.menuBar().addMenu("Help")
        self.whats_new_action = help_menu.addAction("What's New")
        self.whats_new_action.triggered.connect(self.show_whats_new)


    def show_whats_new(self) -> None:
        WhatsNewDialog(__version__, installed_release_notes(), self).exec()

    def _connect_tab(self, tab: DocumentTab) -> None:
        tab.canvas.redact_text_requested.connect(
            lambda: self._from_tab(tab, self.redact_selected_text)
        )
        tab.canvas.redact_area_requested.connect(
            lambda: self._from_tab(tab, self.redact_area)
        )
        tab.canvas.copy_text_requested.connect(
            lambda: self._from_tab(tab, self.copy_selection)
        )
        tab.canvas.area_selected.connect(
            lambda page, bounds: self._from_tab(tab, self._on_area_selected, page, bounds)
        )
        tab.canvas.page_changed.connect(
            lambda page: self._from_tab(tab, self._on_page_changed, page)
        )
        tab.canvas.selection_cancelled.connect(
            lambda: self._from_tab(tab, self._on_selection_cancelled)
        )
        tab.canvas.item_move_requested.connect(
            lambda page, xref, target, bounds: self._from_tab(
                tab, self._on_item_moved, page, xref, target, bounds
            )
        )
        tab.canvas.item_delete_requested.connect(
            lambda page, xref: self._from_tab(tab, self._on_item_deleted, page, xref)
        )

    def _from_tab(self, tab: DocumentTab, handler: Callable, *args) -> None:
        if self._active_tab is tab:
            handler(*args)

    def _remember_active_document(self) -> None:
        tab = self._active_tab
        if tab is None:
            return
        tab.page_index = self.page_index
        tab.zoom = self.zoom
        tab.selection_action = self._selection_action
        tab.active_tool = self._active_tool
        tab.search_query = self.search_bar.query()
        tab.search_open = not self.search_bar.isHidden()
        tab.search_matches = self._search_matches
        tab.search_index = self._search_index

    def _activate_document(self, index: int) -> None:
        self._remember_active_document()
        tab = self.document_tabs.widget(index) if index >= 0 else None
        self._active_tab = tab if isinstance(tab, DocumentTab) else None
        if self._active_tab is None:
            self._show_welcome()
            return
        self._restore_document(self._active_tab)

    def _restore_document(self, tab: DocumentTab) -> None:
        for name in (
            "session", "viewer", "text_boxes", "placed_items", "forms", "signatures", "pages",
            "annotations", "compression", "conversion", "ocr", "redaction", "canvas",
        ):
            setattr(self, name, getattr(tab, name))
        self.page_index = tab.page_index
        self.zoom = tab.zoom
        self._selection_action = tab.selection_action
        self._search_matches = tab.search_matches
        self._search_index = tab.search_index
        self.search_bar.set_query(tab.search_query)
        self.search_bar.set_position(tab.search_index, len(tab.search_matches))
        self.search_bar.setVisible(tab.search_open)
        self._set_active_tool(tab.active_tool)
        self._set_document_actions_enabled(True)
        self.thumbnails.set_document(tab.viewer, tab.viewer.page_count(), tab.page_index)
        self.workspace.setCurrentWidget(self.document_tabs)
        self._update_page_status()
        self._update_tab_title()

    def _show_welcome(self) -> None:
        self.session = self._empty_session
        self.placed_items = PlacedItemService(self.session)
        self.canvas = self._empty_canvas
        self.page_index = 0
        self.zoom = 1.0
        self._selection_action = None
        self._search_matches = []
        self._search_index = -1
        self.search_bar.dismiss()
        self.search_bar.set_query("")
        self._set_active_tool(None)
        self._set_document_actions_enabled(False)
        self.thumbnails.hide()
        self._first_thumbnails = True
        self.workspace.setCurrentWidget(self.welcome)
        self.status.setText("Open a PDF to begin")
        self.setWindowTitle("SABL PDF")

    def _update_tab_title(self) -> None:
        tab = self._active_tab
        if tab is None:
            return
        index = self.document_tabs.indexOf(tab)
        if index >= 0:
            self.document_tabs.setTabText(index, tab.title())
        self.setWindowTitle(f"SABL PDF | {tab.title()}")

    def _open_document(self, path: str | Path) -> None:
        requested = Path(path)
        for index in range(self.document_tabs.count()):
            tab = self.document_tabs.widget(index)
            if tab.session.path and tab.session.path.resolve() == requested.resolve():
                self.document_tabs.setCurrentIndex(index)
                return
        session = (
            self._initial_session
            if not self.document_tabs.count() and self._initial_session is not None
            else DocumentSession()
        )
        session.open(requested)
        tab = DocumentTab(session, self.document_tabs)
        self._connect_tab(tab)
        self.document_tabs.addTab(tab, tab.title())
        self.document_tabs.setCurrentWidget(tab)
        self._refresh()
        if session.open_warnings:
            QMessageBox.warning(
                self, "PDF warnings",
                "This PDF contains damaged or missing objects. Some content may be "
                "unavailable. Review the pages and use Save as to keep the original.",
            )

    def _close_current_tab(self) -> None:
        index = self.document_tabs.currentIndex()
        if index >= 0:
            self._close_document_tab(index)

    def _close_document_tab(self, index: int) -> None:
        tab = self.document_tabs.widget(index)
        if not isinstance(tab, DocumentTab) or not self._confirm_tab_changes(tab):
            return
        if tab is self._active_tab:
            self._active_tab = None
        self.document_tabs.removeTab(index)
        tab.session.close()
        tab.deleteLater()
        if not self.document_tabs.count():
            self._show_welcome()

    def _confirm_tab_changes(self, tab: DocumentTab) -> bool:
        if not tab.session.dirty:
            return True
        choice = QMessageBox.question(
            self, "Unsaved changes",
            f"Save changes to {tab.title()} before closing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            return False
        if choice == QMessageBox.StandardButton.Discard:
            return True
        if choice != QMessageBox.StandardButton.Save:
            return False
        self.document_tabs.setCurrentWidget(tab)
        if tab.session.path is None:
            self.save_as()
        else:
            self._run(lambda: tab.session.save())
        if not tab.session.dirty:
            self._update_tab_title()
        return not tab.session.dirty

    def _build_thumbnails(self) -> None:
        self.thumbnails = PageThumbnails(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.thumbnails)
        self.view_menu = self.menuBar().addMenu("View")
        self.view_menu.addAction(self.thumbnails.toggleViewAction())
        self.thumbnails.page_selected.connect(self._jump_to_page)
        self.thumbnails.hide()
        self._first_thumbnails = True

    def _jump_to_page(self, index: int) -> None:
        if self._require_document():
            self.page_index = index
            self.canvas.scroll_to_page(index)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Quick access", self)
        self._quick_toolbar = toolbar
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
        self._toolbar_button(
            toolbar, "text", "Add Text", self.add_text_box, "SP_FileIcon", "Ctrl+Shift+T"
        )
        self._toolbar_button(
            toolbar, "highlight", "Highlight",
            lambda: self.mark_selection("highlight"), "SP_DialogApplyButton", "Ctrl+Shift+H",
        )
        self._toolbar_button(
            toolbar, "sign", "Sign", self.draw_signature, "SP_FileDialogInfoView", "Ctrl+Alt+S"
        )
        toolbar.addSeparator()
        self._toolbar_button(
            toolbar, "rotate", "Rotate", self.rotate_page, "SP_BrowserReload", "Ctrl+Shift+R"
        )
        self._toolbar_button(
            toolbar, "compress", "Compress", self.compress_pdf, "SP_DriveHDIcon",
            "Ctrl+Shift+C"
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
            self.addAction(action)
        if key in {"text", "highlight", "sign"}:
            action.setCheckable(True)
        action.triggered.connect(lambda _checked=False: self._invoke_quick_action(key, handler))
        toolbar.addAction(action)
        self.quick_actions[key] = action

    def _build_toolbar_preferences(self) -> None:
        menu = self.view_menu.addMenu("Customize toolbar")
        self.toolbar_toggles: dict[str, QAction] = {}
        for key, action in self.quick_actions.items():
            toggle = menu.addAction(action.text())
            toggle.setCheckable(True)
            toggle.setChecked(
                self._ui_settings.value(f"toolbar/{key}", True, type=bool)
            )
            toggle.toggled.connect(
                lambda checked, action_key=key: self._set_toolbar_visible(action_key, checked)
            )
            self.toolbar_toggles[key] = toggle
        menu.addSeparator()
        menu.addAction("Reset toolbar", self._reset_toolbar)
        self._refresh_toolbar()

    def _set_toolbar_visible(self, key: str, visible: bool) -> None:
        self._ui_settings.setValue(f"toolbar/{key}", visible)
        self._refresh_toolbar()

    def _reset_toolbar(self) -> None:
        for action in self.toolbar_toggles.values():
            action.setChecked(True)

    def _refresh_toolbar(self) -> None:
        self._quick_toolbar.clear()
        for group in (("open", "save", "find"), ("text", "highlight", "sign"), ("rotate", "compress")):
            available = [self.quick_actions[key] for key in group if self.toolbar_toggles[key].isChecked()]
            if available:
                if self._quick_toolbar.actions():
                    self._quick_toolbar.addSeparator()
                self._quick_toolbar.addActions(available)

    def _invoke_quick_action(self, key: str, handler: Callable) -> None:
        handler()
        if key in {"text", "highlight", "sign"} and self._selection_action is None:
            self._set_active_tool(None)

    def _build_navigation_toolbar(self) -> None:
        navigation = QToolBar("Page navigation", self)
        navigation.setObjectName("page_navigation")
        navigation.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, navigation)
        self.navigation_actions: list[QAction] = []
        for text, handler in [
            ("Previous", lambda: self.change_page(-1)),
            ("Next", lambda: self.change_page(1)),
            ("Zoom Out", lambda: self.change_zoom(0.8)),
            ("Zoom In", lambda: self.change_zoom(1.25)),
        ]:
            action = QAction(text, self)
            action.triggered.connect(handler)
            navigation.addAction(action)
            self.navigation_actions.append(action)

    def _build_cancel_shortcut(self) -> None:
        cancel_action = QAction(self)
        cancel_action.setShortcut(QKeySequence("Escape"))
        cancel_action.triggered.connect(self._cancel_active_tool)
        self.addAction(cancel_action)

    def _set_document_actions_enabled(self, enabled: bool) -> None:
        for action in self._document_actions:
            action.setEnabled(enabled)
        for key, action in self.quick_actions.items():
            action.setEnabled(enabled or key == "open")
        for action in self.navigation_actions:
            action.setEnabled(enabled)

    def _set_active_tool(self, name: str | None) -> None:
        self._active_tool = name
        for key, label in {"text": "Add Text", "highlight": "Highlight", "sign": "Sign"}.items():
            self.quick_actions[key].setChecked(name == label)

    def _cancel_active_tool(self) -> None:
        if self._selection_action is not None:
            self.canvas.cancel_selection()
        elif self.search_bar.isVisible():
            self._close_search()
        else:
            self.canvas.clear_item_selection()
            self.canvas.clear_text_selection()


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
        self.workspace.setCurrentWidget(self.document_tabs)
        self._set_document_actions_enabled(True)
        if len(document) == 0:
            self.status.setText("No pages")
            self.canvas.display_pages([], self.viewer.render, self.zoom)
            self._update_tab_title()
            return
        requested_page = min(max(0, self.page_index), len(document) - 1)
        self.canvas.display_pages(
            self.viewer.page_sizes(),
            lambda index: self.viewer.render(index, self.zoom),
            self.zoom,
        )
        self.canvas.set_text_selector(self.viewer.select_text)
        self.canvas.set_placed_items([
            (item.page, item.xref, item.bounds) for item in self.placed_items.list()
        ])
        self.page_index = requested_page
        self.thumbnails.set_document(self.viewer, len(document), requested_page)
        if self._first_thumbnails:
            self.thumbnails.show()
            self._first_thumbnails = False
        self.canvas.scroll_to_page(requested_page)
        self._update_page_status()
        self._update_tab_title()

    def _update_page_status(self) -> None:
        self.status.setText(
            f"Page {self.page_index + 1} / {self.viewer.page_count()} | {round(self.zoom * 100)}%"
        )

    def _on_page_changed(self, page_index: int) -> None:
        self.page_index = page_index
        if hasattr(self, "thumbnails"):
            self.thumbnails.select_page(page_index)
        self._update_page_status()


    def _after_edit(self) -> None:
        self._refresh()
        if self.search_bar.query():
            self._search_query(self.search_bar.query())


    def _confirm_changes(self) -> bool:
        return all(
            self._confirm_tab_changes(self.document_tabs.widget(index))
            for index in range(self.document_tabs.count())
        )


    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._confirm_changes():
            event.ignore()
            return
        for index in range(self.document_tabs.count()):
            self.document_tabs.widget(index).session.close()
        self._empty_session.close()
        event.accept()


    def _select_area(
        self,
        callback: Callable[[tuple], None],
        click_size: tuple[float, float] | None = None,
        preview_strokes: list[list[tuple[float, float]]] | None = None,
        preview_label: str | None = None,
        preview_image: str | None = None,
        tool_name: str = "Select area",
    ) -> None:
        if not self._require_document():
            return
        self._selection_action = callback
        self.canvas.clear_item_selection()
        self._set_active_tool(tool_name)
        self.canvas.set_selection_enabled(
            True, click_size, preview_strokes, preview_label, preview_image
        )
        self.status.setText(
            "Click to place or drag to size; right-click to cancel"
            if click_size else "Drag a rectangle on the page; right-click to cancel"
        )

    def _on_selection_cancelled(self) -> None:
        self._selection_action = None
        self._set_active_tool(None)
        self._update_page_status()


    def _on_area_selected(self, page_index: int, rect: tuple) -> None:
        self.page_index = page_index
        action = self._selection_action
        self._selection_action = None
        self._set_active_tool(None)
        if action is not None:
            self._run(lambda: action(rect))

    def _on_item_moved(self, page: int, xref: int, target: int, bounds: tuple) -> None:
        def move() -> None:
            self.placed_items.move(page, xref, bounds, target_page_index=target)
            self.page_index = target
            self._after_edit()
        self._run(move)

    def _on_item_deleted(self, page: int, xref: int) -> None:
        def delete() -> None:
            self.placed_items.delete(page, xref)
            self.page_index = page
            self._after_edit()
        self._run(delete)
