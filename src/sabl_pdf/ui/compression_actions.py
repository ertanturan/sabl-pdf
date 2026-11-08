from PySide6.QtWidgets import QFileDialog


class CompressionActions:

    def compress_pdf(self) -> None:
        if not self._require_document():
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Optimised PDF", "", "PDF (*.pdf)")
        if filename:
            self._run(lambda: self.compression.optimise(filename))
