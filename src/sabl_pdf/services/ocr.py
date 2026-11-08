from pathlib import Path
from typing import Protocol

import fitz

from sabl_pdf.core.session import DocumentSession


class PageOcrEngine(Protocol):
    def extract(self, page: fitz.Page, language: str) -> str: ...


class TesseractPageOcr:
    def extract(self, page: fitz.Page, language: str) -> str:
        try:
            text_page = page.get_textpage_ocr(language=language, full=True)
        except RuntimeError as exc:
            raise RuntimeError("OCR requires Tesseract OCR language data on this computer") from exc
        return page.get_text("text", textpage=text_page)


class OcrService:
    def __init__(self, session: DocumentSession, engine: PageOcrEngine | None = None) -> None:
        self._session = session
        self._engine = engine or TesseractPageOcr()

    def extract(self, page_index: int, language: str = "eng") -> str:
        if not language or not language.isalpha():
            raise ValueError("Enter a valid OCR language code")
        return self._engine.extract(self._session.document[page_index], language)

    def export_text(self, destination: str | Path, language: str = "eng") -> Path:
        text = "\n\n".join(self.extract(index, language) for index in range(len(self._session.document)))
        output = Path(destination)
        output.write_text(text, encoding="utf-8")
        return output
