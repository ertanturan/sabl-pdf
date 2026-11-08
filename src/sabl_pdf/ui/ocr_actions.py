from PySide6.QtWidgets import QFileDialog, QMessageBox


class OcrActions:

    def ocr_page(self) -> None:
        if not self._require_document():
            return
        def perform() -> None:
            content = self.ocr.extract(self.page_index)
            dialog = QMessageBox(self)
            dialog.setWindowTitle("OCR result")
            dialog.setText(content[:400] if content else "No text found")
            dialog.setDetailedText(content)
            dialog.exec()
        self._run(perform)

    def export_ocr(self) -> None:
        if not self._require_document():
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export OCR text", "", "Text (*.txt)")
        if filename:
            self._run(lambda: self.ocr.export_text(filename))
