from PySide6.QtWidgets import QFileDialog, QDialog
from sabl_pdf.ui.signature_pad import SignatureDialog


class SignatureActions:

    def import_signature(self) -> None:
        if not self._require_document():
            return
        filename, _ = QFileDialog.getOpenFileName(self, "Signature image", "", "Images (*.png *.jpg *.jpeg)")
        if filename:
            self._select_area(lambda bounds: (self.signatures.import_image(self.page_index, bounds, filename), self._after_edit()))

    def draw_signature(self) -> None:
        if not self._require_document():
            return
        dialog = SignatureDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            strokes = dialog.surface.strokes
            self._select_area(lambda bounds: (self.signatures.draw(self.page_index, bounds, strokes), self._after_edit()))
