from PySide6.QtWidgets import QInputDialog, QMessageBox


class TextActions:

    def add_text_box(self) -> None:
        def add(bounds) -> None:
            text, accepted = QInputDialog.getMultiLineText(self, "Add text", "Text")
            if accepted and text.strip():
                self.text_boxes.add(self.page_index, bounds, text)
                self._after_edit()
        self._select_area(add, click_size=(190, 55))

    def _choose_text_box(self) -> int | None:
        if not self._require_document():
            return None
        items = self.text_boxes.list(self.page_index)
        if not items:
            QMessageBox.information(self, "Text boxes", "There are no added text boxes")
            return None
        labels = [f"{item.xref}: {item.content[:40]}" for item in items]
        chosen, accepted = QInputDialog.getItem(self, "Text boxes", "Choose a text box", labels, 0, False)
        return items[labels.index(chosen)].xref if accepted else None

    def edit_text_box(self) -> None:
        xref = self._choose_text_box()
        if xref is None:
            return
        original = next(item.content for item in self.text_boxes.list(self.page_index) if item.xref == xref)
        text, accepted = QInputDialog.getMultiLineText(self, "Edit text", "Text", original)
        if accepted:
            self._run(lambda: (self.text_boxes.update(self.page_index, xref, text), self._after_edit()))

    def remove_text_box(self) -> None:
        xref = self._choose_text_box()
        if xref is not None:
            self._run(lambda: (self.text_boxes.remove(self.page_index, xref), self._after_edit()))

    def fill_form(self) -> None:
        if not self._require_document():
            return
        fields = self.forms.list_fields(self.page_index)
        if not fields:
            QMessageBox.information(self, "Forms", "This page has no supported form fields")
            return
        names = [field.name for field in fields]
        selected, accepted = QInputDialog.getItem(self, "Fill form", "Field", names, 0, False)
        if not accepted:
            return
        current = fields[names.index(selected)].value or ""
        value, accepted = QInputDialog.getText(self, "Fill form", selected, text=current)
        if accepted:
            self._run(lambda: (self.forms.set_value(self.page_index, selected, value), self._after_edit()))
