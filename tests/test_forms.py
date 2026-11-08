import fitz
import pytest

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.forms import FormService


def test_text_form_value(session: DocumentSession) -> None:
    widget = fitz.Widget()
    widget.field_name = "Full name"
    widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    widget.rect = fitz.Rect(20, 100, 220, 120)
    session.document[0].add_widget(widget)
    service = FormService(session)

    service.set_value(0, "Full name", "Ada Lovelace")
    fields = service.list_fields(0)

    assert fields[0].name == "Full name"
    assert fields[0].value == "Ada Lovelace"


def test_missing_form_field_is_rejected(session: DocumentSession) -> None:
    service = FormService(session)

    with pytest.raises(ValueError, match="not found"):
        service.set_value(0, "Absent", "Any")
