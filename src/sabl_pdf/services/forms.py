from dataclasses import dataclass

import fitz

from sabl_pdf.core.session import DocumentSession


@dataclass(frozen=True)
class FormField:
    name: str
    value: str | None
    field_type: int


class FormService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def list_fields(self, page_index: int) -> list[FormField]:
        widgets = self._session.document[page_index].widgets() or ()
        return [FormField(widget.field_name, widget.field_value, widget.field_type) for widget in widgets]

    def set_value(self, page_index: int, name: str, value: str) -> None:
        for widget in self._session.document[page_index].widgets() or ():
            if widget.field_name == name:
                if widget.field_type not in {fitz.PDF_WIDGET_TYPE_TEXT, fitz.PDF_WIDGET_TYPE_CHECKBOX}:
                    raise ValueError("Unsupported form field type")
                if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    widget.field_value = widget.on_state() if value.lower() in {"yes", "true", "1"} else "Off"
                else:
                    widget.field_value = value
                widget.update()
                self._session.mark_dirty()
                return
        raise ValueError(f"Form field not found: {name}")
