from typing import Literal

import fitz

from sabl_pdf.core.session import DocumentSession


class AnnotationService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def mark_text(self, page_index: int, bounds: tuple[float, float, float, float],
                  style: Literal["highlight", "underline"]) -> int:
        rect = fitz.Rect(bounds)
        if rect.is_empty:
            raise ValueError("Select an area containing text")
        page = self._session.document[page_index]
        if style == "highlight":
            annot = page.add_highlight_annot(rect)
        elif style == "underline":
            annot = page.add_underline_annot(rect)
        else:
            raise ValueError("Unsupported annotation style")
        self._session.mark_dirty()
        return annot.xref

    def add_note(self, page_index: int, position: tuple[float, float], text: str) -> int:
        if not text.strip():
            raise ValueError("Note cannot be empty")
        annot = self._session.document[page_index].add_text_annot(position, text)
        self._session.mark_dirty()
        return annot.xref

    def remove(self, page_index: int, xref: int) -> None:
        page = self._session.document[page_index]
        annot = page.load_annot(xref)
        if annot is None:
            raise ValueError("Annotation not found")
        page.delete_annot(annot)
        self._session.mark_dirty()
