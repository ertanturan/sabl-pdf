from pathlib import Path
import fitz
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox


class ViewerActions:

    def open_pdf(self) -> None:
        if not self._confirm_changes():
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF (*.pdf)")
        if filename:
            self.open_path(filename)

    def open_path(self, path: str | Path) -> None:
        def action() -> None:
            self.session.open(path)
            self.page_index = 0
            self._search_matches = []
            self._search_index = -1
            self._refresh()
            if self.search_bar.query():
                self._search_query(self.search_bar.query())
            if self.session.open_warnings:
                QMessageBox.warning(
                    self, "PDF warnings",
                    "This PDF contains damaged or missing objects. Some content may be "
                    "unavailable. Review the pages and use Save as to keep the original.",
                )
        self._run(action)

    def save_pdf(self) -> None:
        if not self._require_document():
            return
        if self.session.path is None:
            self.save_as()
            return
        self._run(lambda: (self.session.save(), self._refresh()))

    def save_as(self) -> None:
        if not self._require_document():
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF (*.pdf)")
        if filename:
            self._run(lambda: (self.session.save(filename), self._refresh()))

    def change_page(self, difference: int) -> None:
        if self._require_document():
            self.page_index = max(0, min(self.page_index + difference, self.viewer.page_count() - 1))
            self.canvas.scroll_to_page(self.page_index)
            self._update_page_status()

    def change_zoom(self, factor: float) -> None:
        if self._require_document():
            self.zoom = max(0.25, min(4.0, self.zoom * factor))
            self._refresh()

    def search_text(self) -> None:
        if self._require_document():
            self.search_bar.focus_query()

    def _search_query(self, query: str) -> None:
        self._search_matches = self.viewer.search(query) if query.strip() else []
        self._search_index = 0 if self._search_matches else -1
        self._show_search_match()

    def _move_search(self, difference: int) -> None:
        if not self._search_matches:
            return
        self._search_index = (self._search_index + difference) % len(self._search_matches)
        self._show_search_match()

    def _show_search_match(self) -> None:
        self.search_bar.set_position(self._search_index, len(self._search_matches))
        if self._search_index < 0:
            self.canvas.clear_search_highlight()
            return
        match = self._search_matches[self._search_index]
        self.page_index = match.page
        self.canvas.scroll_to_page(match.page)
        self.canvas.highlight(match.bounds, match.page)

    def _close_search(self) -> None:
        self.search_bar.hide()
        self._search_matches = []
        self._search_index = -1
        self.canvas.clear_search_highlight()

    def copy_page_text(self) -> None:
        if self._require_document():
            QApplication.clipboard().setText(self.viewer.text(self.page_index))

    def copy_selection(self) -> None:
        if self._require_document():
            def copy(bounds) -> None:
                page = self.session.document[self.page_index]
                QApplication.clipboard().setText(page.get_textbox(fitz.Rect(bounds)))
            self._select_area(copy)
