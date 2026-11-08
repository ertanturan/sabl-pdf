import pytest

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.text_boxes import TextBoxService


def test_text_box_lifecycle(session: DocumentSession) -> None:
    service = TextBoxService(session)

    xref = service.add(0, (25, 80, 250, 125), "First")
    service.update(0, xref, "Revised")
    found = service.list(0)

    assert len(found) == 1
    assert found[0].content == "Revised"
    assert session.dirty is True

    service.remove(0, xref)

    assert service.list(0) == []


def test_empty_text_is_rejected(session: DocumentSession) -> None:
    service = TextBoxService(session)

    with pytest.raises(ValueError):
        service.add(0, (0, 0, 100, 20), " ")
