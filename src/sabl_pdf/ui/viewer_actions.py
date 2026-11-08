from pathlib import Path
import fitz
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox


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
            self._refresh()
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
        if not self._require_document():
            return
        query, accepted = QInputDialog.getText(self, "Search", "Find text")
        if accepted and query.strip():
            matches = self.viewer.search(query)
            if not matches:
                QMessageBox.information(self, "Search", "No matches found")
                return
            match = matches[0]
            self.page_index = match.page
            self.canvas.scroll_to_page(match.page)
            self.canvas.highlight(match.bounds, match.page)
            self.status.setText(f"{len(matches)} matches | showing first on page {match.page + 1}")

    def copy_page_text(self) -> None:
        if self._require_document():
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(self.viewer.text(self.page_index))

    def copy_selection(self) -> None:
        if self._require_document():
            def copy(bounds) -> None:
                from PySide6.QtWidgets import QApplication
                page = self.session.document[self.page_index]
                QApplication.clipboard().setText(page.get_textbox(fitz.Rect(bounds)))
            self._select_area(copy)
