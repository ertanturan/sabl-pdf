from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QInputDialog, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QVBoxLayout,
)

from sabl_pdf.services.redaction import RedactionTarget


class RedactionReviewDialog(QDialog):
    def __init__(self, targets: list[RedactionTarget], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Review redaction matches")
        self.resize(500, 380)
        self.targets = targets
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose the locations to remove from the exported copy:"))
        self.items = QListWidget(self)
        for number, target in enumerate(targets, start=1):
            item = QListWidgetItem(f"Page {target.page + 1}, match {number}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.items.addItem(item)
        layout.addWidget(self.items)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected(self) -> list[RedactionTarget]:
        return [
            target for index, target in enumerate(self.targets)
            if self.items.item(index).checkState() == Qt.CheckState.Checked
        ]


class RedactionActions:
    def redact_information(self) -> None:
        if not self._require_document():
            return
        phrase, accepted = QInputDialog.getText(
            self, "Redact information", "What information would you like to redact?"
        )
        if not accepted or not phrase.strip():
            return
        try:
            matches = self.redaction.find(phrase)
        except Exception as exc:
            QMessageBox.warning(self, "Redaction unavailable", str(exc))
            return
        if not matches:
            QMessageBox.information(
                self, "No matches",
                "No matching text was found. This does not prove the information is absent.",
            )
            return
        review = RedactionReviewDialog(matches, self)
        if review.exec() != QDialog.DialogCode.Accepted:
            return
        self._confirm_redaction(review.selected())

    def redact_selected_text(self) -> None:
        if not self._require_document():
            return
        selection = self.canvas.selected_text_regions()
        if selection is None:
            QMessageBox.information(self, "Redact selection", "Select text in the PDF first.")
            return
        targets = [
            RedactionTarget(selection.page, bounds, selection.text)
            for bounds in selection.rects
        ]
        self._confirm_redaction(targets)

    def redact_area(self) -> None:
        self._select_area(
            self._redact_selected_area, preview_label="Redact", tool_name="Redact area"
        )

    def _redact_selected_area(self, bounds: tuple) -> None:
        target = self.redaction.area_target(self.page_index, bounds)
        self._confirm_redaction([target])

    def _confirm_redaction(self, targets: list[RedactionTarget]) -> None:
        if not targets:
            QMessageBox.information(self, "Redact information", "No areas were selected.")
            return
        answer = QMessageBox.warning(
            self, "Permanent redaction",
            "This creates a new image-only PDF with blacked-out regions. "
            "It permanently removes all original PDF content and hidden objects "
            "from the new copy, but selectable text, links, forms, vector quality "
            "and digital signatures will be lost. The original file is unchanged. "
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        source = self.session.path
        suggested = (
            str(source.with_name(source.stem + ".redacted.pdf"))
            if source is not None else ""
        )
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save verified redacted copy", suggested, "PDF (*.pdf)"
        )
        if not filename:
            return
        try:
            report = self.redaction.export(targets, Path(filename))
        except Exception as exc:
            QMessageBox.critical(self, "Redaction failed", str(exc))
            return
        self.canvas.clear_text_selection()
        self.canvas.clear_search_highlight()
        QMessageBox.information(
            self, "Redaction verified",
            f"Saved {report.regions} redacted region(s) across "
            f"{report.pages} page(s) to:\n{report.output}",
        )
