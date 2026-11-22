from PySide6.QtWidgets import QInputDialog


class AnnotationActions:

    def mark_selection(self, style: str) -> None:
        self._select_area(
            lambda bounds: (self.annotations.mark_text(self.page_index, bounds, style), self._after_edit()),
            preview_label=style.title(),
            tool_name=style.title(),
        )

    def add_note(self) -> None:
        def place(bounds) -> None:
            note, accepted = QInputDialog.getMultiLineText(self, "Add note", "Note")
            if accepted and note.strip():
                self.annotations.add_note(self.page_index, (bounds[0], bounds[1]), note)
                self._after_edit()
        self._select_area(place, click_size=(22, 22), preview_label="N", tool_name="Add note")

    def remove_annotation(self) -> None:
        if not self._require_document():
            return
        page = self.session.document[self.page_index]
        annots = list(page.annots() or ())
        if not annots:
            return
        choices = [f"{a.xref}: {a.type[1]}" for a in annots]
        choice, accepted = QInputDialog.getItem(self, "Remove annotation", "Annotation", choices, 0, False)
        if accepted:
            index = choices.index(choice)
            self._run(lambda: (self.annotations.remove(self.page_index, annots[index].xref), self._after_edit()))
