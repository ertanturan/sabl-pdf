from pathlib import Path

import fitz
import pytest

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.pages import PageService


def test_merge_pdf(session: DocumentSession, sample_pdf: Path) -> None:
    service = PageService(session)

    service.merge(sample_pdf)

    assert len(session.document) == 2
    assert session.dirty


def test_rotate_page(session: DocumentSession) -> None:
    service = PageService(session)

    service.rotate(0)

    assert session.document[0].rotation == 90


def test_reorder_pages(session: DocumentSession, sample_pdf: Path) -> None:
    service = PageService(session)
    service.merge(sample_pdf)
    session.document[1].insert_text((30, 200), "Last page")

    service.reorder([1, 0])

    assert "Last page" in session.document[0].get_text()


def test_split_creates_separate_pdf(session: DocumentSession, tmp_path: Path) -> None:
    service = PageService(session)
    target = tmp_path / "part.pdf"

    output = service.split(target, 0, 0)

    with fitz.open(output) as doc:
        assert len(doc) == 1


def test_delete_only_page_rejected(session: DocumentSession) -> None:
    service = PageService(session)

    with pytest.raises(ValueError):
        service.delete(0)
