from dataclasses import dataclass

import fitz

from sabl_pdf.core.session import DocumentSession


@dataclass(frozen=True)
class TextBox:
    xref: int
    content: str
    bounds: tuple[float, float, float, float]


class TextBoxService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def add(self, page_index: int, bounds: tuple[float, float, float, float], text: str) -> int:
        if not text.strip():
            raise ValueError("Text cannot be empty")
        rect = fitz.Rect(bounds)
        if rect.is_empty or rect.is_infinite:
            raise ValueError("Select a valid text area")
        annot = self._session.document[page_index].add_freetext_annot(rect, text, fontsize=12)
        self._session.mark_dirty()
        return annot.xref

    def list(self, page_index: int) -> list[TextBox]:
        page = self._session.document[page_index]
        return [
            TextBox(annot.xref, annot.info.get("content", ""), tuple(annot.rect))
            for annot in page.annots() or ()
            if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT
        ]

    def update(self, page_index: int, xref: int, text: str) -> None:
        if not text.strip():
            raise ValueError("Text cannot be empty")
        page = self._session.document[page_index]
        annot = self._get_text_box(page, xref)
        annot.set_info(content=text)
        annot.update()
        self._session.mark_dirty()

    def remove(self, page_index: int, xref: int) -> None:
        page = self._session.document[page_index]
        annot = self._get_text_box(page, xref)
        page.delete_annot(annot)
        self._session.mark_dirty()

    def _get_text_box(self, page: fitz.Page, xref: int) -> fitz.Annot:
        annot = page.load_annot(xref)
        if annot is None or annot.type[0] != fitz.PDF_ANNOT_FREE_TEXT:
            raise ValueError("Text box not found")
        return annot
