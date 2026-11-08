from PySide6.QtWidgets import QFileDialog


class ConversionActions:

    def add_images(self) -> None:
        filenames, _ = QFileDialog.getOpenFileNames(self, "Add images", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not filenames:
            return
        if not self._require_document():
            return
        self._run(lambda: (self.conversion.images_to_pdf(filenames), self._after_edit()))

    def export_images(self) -> None:
        if not self._require_document():
            return
        directory = QFileDialog.getExistingDirectory(self, "Export pages")
        if directory:
            self._run(lambda: self.conversion.pdf_to_images(directory))
