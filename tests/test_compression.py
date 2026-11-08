from pathlib import Path

import fitz
import pytest

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.compression import CompressionService


def test_optimise_produces_readable_pdf(session: DocumentSession, tmp_path: Path) -> None:
    destination = tmp_path / "optimised.pdf"
    service = CompressionService(session)

    result = service.optimise(destination)

    with fitz.open(result) as output:
        assert "Hello SABL" in output[0].get_text()


def test_same_file_rejected(session: DocumentSession) -> None:
    service = CompressionService(session)

    with pytest.raises(ValueError):
        service.optimise(session.path)


def test_image_quality_is_validated(session: DocumentSession, tmp_path: Path) -> None:
    service = CompressionService(session)

    with pytest.raises(ValueError):
        service.optimise(tmp_path / "out.pdf", image_quality=0)


def test_compression_does_not_mutate_open_document(session: DocumentSession, tmp_path: Path) -> None:
    service = CompressionService(session)
    original = session.document[0].get_text()

    service.optimise(tmp_path / "result.pdf")

    assert session.document[0].get_text() == original
    assert session.dirty is False
