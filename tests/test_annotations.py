import fitz
import pytest

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.annotations import AnnotationService


def test_highlight_text(session: DocumentSession) -> None:
    service = AnnotationService(session)
    bounds = tuple(session.document[0].search_for("Hello")[0])

    xref = service.mark_text(0, bounds, "highlight")

    page = session.document[0]
    assert page.load_annot(xref).type[0] == fitz.PDF_ANNOT_HIGHLIGHT


def test_underline_text(session: DocumentSession) -> None:
    service = AnnotationService(session)
    bounds = tuple(session.document[0].search_for("Hello")[0])

    xref = service.mark_text(0, bounds, "underline")

    page = session.document[0]
    assert page.load_annot(xref).type[0] == fitz.PDF_ANNOT_UNDERLINE


def test_create_note_then_remove(session: DocumentSession) -> None:
    service = AnnotationService(session)

    xref = service.add_note(0, (100, 80), "Remember this")
    service.remove(0, xref)

    assert not list(session.document[0].annots() or ())


def test_note_rejects_empty_body(session: DocumentSession) -> None:
    service = AnnotationService(session)

    with pytest.raises(ValueError):
        service.add_note(0, (50, 50), " ")
