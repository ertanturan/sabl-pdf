from dataclasses import dataclass

import fitz

from sabl_pdf.core.session import DocumentSession


@dataclass(frozen=True)
class SearchMatch:
    page: int
    bounds: tuple[float, float, float, float]


class ViewerService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

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
        for page_number, page in enumerate(self._session.document):
            for rect in page.search_for(query):
                matches.append(SearchMatch(page_number, tuple(rect)))
        return matches
