from pathlib import Path

import fitz
import pytest

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.ocr import OcrService


class FakeOcrEngine:
    def extract(self, page: fitz.Page, language: str) -> str:
        return f"OCR {page.number} {language}"


def test_ocr_uses_injected_engine(session: DocumentSession) -> None:
    service = OcrService(session, FakeOcrEngine())

    text = service.extract(0)

    assert text == "OCR 0 eng"


def test_ocr_exports_text(session: DocumentSession, tmp_path: Path) -> None:
    target = tmp_path / "output.txt"
    service = OcrService(session, FakeOcrEngine())

    result = service.export_text(target)

    assert result.read_text() == "OCR 0 eng"


def test_ocr_rejects_invalid_language(session: DocumentSession) -> None:
    service = OcrService(session, FakeOcrEngine())

    with pytest.raises(ValueError):
        service.extract(0, "en-1")
