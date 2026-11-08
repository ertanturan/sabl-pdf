import json
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog, QDialog, QMessageBox

from sabl_pdf.ui.signature_pad import SignatureDialog


class SignatureActions:
    def import_signature(self) -> None:
        if not self._require_document():
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, "Signature image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if filename:
            self._select_area(
                lambda bounds: (
                    self.signatures.import_image(self.page_index, bounds, filename),
                    self._after_edit(),
                ),
                click_size=(180, 70),
                tool_name="Sign",
            )

    def draw_signature(self) -> None:
        if not self._require_document():
            return
        dialog = SignatureDialog(self, self._load_saved_signature())
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        strokes = dialog.surface.strokes
        if not any(len(stroke) >= 2 for stroke in strokes):
            QMessageBox.information(self, "Signature", "Draw a signature before placing it.")
            return
        self._save_signature(strokes)
        self._place_signature(strokes)

    def use_saved_signature(self) -> None:
        if not self._require_document():
            return
        strokes = self._load_saved_signature()
        if not strokes:
            QMessageBox.information(self, "Signature", "Draw a signature first.")
            return
        self._place_signature(strokes)

    def _place_signature(self, strokes: list[list[tuple[float, float]]]) -> None:
        self._select_area(
            lambda bounds: (
                self.signatures.draw(self.page_index, bounds, strokes),
                self._after_edit(),
            ),
            click_size=(180, 70),
            preview_strokes=strokes,
            tool_name="Sign",
        )

    def _signature_settings(self) -> QSettings:
        return QSettings("SABL", "SABL PDF")

    def _load_saved_signature(self) -> list[list[tuple[float, float]]]:
        value = self._signature_settings().value("signature_strokes", "")
        if not value:
            return []
        try:
            strokes = json.loads(value)
            result = [[(float(x), float(y)) for x, y in stroke] for stroke in strokes]
            return result if any(len(stroke) >= 2 for stroke in result) else []
        except (TypeError, ValueError, KeyError):
            return []

    def _save_signature(self, strokes: list[list[tuple[float, float]]]) -> None:
        self._signature_settings().setValue("signature_strokes", json.dumps(strokes))
