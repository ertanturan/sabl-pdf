from dataclasses import dataclass

import fitz

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.ocr_text import OcrTextPages
from sabl_pdf.services.text_selection import TextSelection, TextSelectionService


@dataclass(frozen=True)
class SearchMatch:
    page: int
    bounds: tuple[float, float, float, float]


class ViewerService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session
        self._ocr_pages = OcrTextPages(session)
        self._selection = TextSelectionService(session, self._ocr_pages)

    def page_count(self) -> int:
        return len(self._session.document)

    def page_sizes(self) -> list[tuple[float, float]]:
        return [(page.rect.width, page.rect.height) for page in self._session.document]

    def render(self, page: int, zoom: float = 1.0) -> fitz.Pixmap:
        if zoom <= 0 or zoom > 8:
            raise ValueError("Zoom must be greater than zero and at most 8")
        return self._session.document[page].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)

    def text(self, page: int) -> str:
        return self._session.document[page].get_text()

    def search(self, query: str) -> list[SearchMatch]:
        if not query.strip():
            return []
        matches: list[SearchMatch] = []
        ocr_error: RuntimeError | None = None
        for page_number, page in enumerate(self._session.document):
            found = page.search_for(query)
            if not found and self._ocr_pages.is_candidate(page):
                try:
                    ocr_page, textpage = self._ocr_pages.get(page_number)
                    found = ocr_page.search_for(query, textpage=textpage)
                except RuntimeError as exc:
                    ocr_error = exc
                    continue
            for rect in found:
                displayed = rect * page.rotation_matrix
                matches.append(SearchMatch(page_number, tuple(displayed)))
        if not matches and ocr_error is not None:
            raise ocr_error
        return matches

    def clear_ocr_cache(self) -> None:
        self._ocr_pages.clear()

    def select_text(
        self, page: int, start: tuple[float, float], end: tuple[float, float]
    ) -> TextSelection | None:
        return self._selection.select(page, start, end)
