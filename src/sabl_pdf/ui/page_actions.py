from PySide6.QtWidgets import QFileDialog, QInputDialog


class PageActions:

    def merge_pdf(self) -> None:
        if not self._require_document():
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Merge PDF", "", "PDF (*.pdf)")
        if filename:
            self._run(lambda: (self.pages.merge(filename), self._after_edit()))

    def split_pdf(self) -> None:
        if not self._require_document():
            return
        maximum = self.viewer.page_count()
        first, ok = QInputDialog.getInt(self, "Split PDF", "First page", 1, 1, maximum)
        if not ok:
            return
        last, ok = QInputDialog.getInt(self, "Split PDF", "Last page", maximum, first, maximum)
        if not ok:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Split PDF", "", "PDF (*.pdf)")
        if filename:
            self._run(lambda: self.pages.split(filename, first - 1, last - 1))

    def delete_page(self) -> None:
        if self._require_document():
            self._run(lambda: (self.pages.delete(self.page_index), self._after_edit()))

    def rotate_page(self) -> None:
        if self._require_document():
            self._run(lambda: (self.pages.rotate(self.page_index), self._after_edit()))

    def move_page(self, direction: int) -> None:
        if not self._require_document():
            return
        other = self.page_index + direction
        if not 0 <= other < self.viewer.page_count():
            return
        order = list(range(self.viewer.page_count()))
        order[self.page_index], order[other] = order[other], order[self.page_index]
        self._run(lambda: self.pages.reorder(order))
        self.page_index = other
        self._refresh()
