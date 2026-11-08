from pathlib import Path

import fitz

from sabl_pdf.core.session import DocumentSession


class PageService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def merge(self, path: str | Path) -> None:
        with fitz.open(path) as source:
            if not source.is_pdf or len(source) == 0:
                raise ValueError("Select a PDF containing pages")
            self._session.document.insert_pdf(source)
        self._session.mark_dirty()

    def delete(self, index: int) -> None:
        document = self._session.document
        if len(document) <= 1:
            raise ValueError("Cannot delete the only page")
        document.delete_page(index)
        self._session.mark_dirty()

    def rotate(self, index: int, clockwise: int = 90) -> None:
        if clockwise % 90 != 0:
            raise ValueError("Rotation must be a multiple of 90 degrees")
        page = self._session.document[index]
        page.set_rotation((page.rotation + clockwise) % 360)
        self._session.mark_dirty()

    def reorder(self, indexes: list[int]) -> None:
        document = self._session.document
        if sorted(indexes) != list(range(len(document))):
            raise ValueError("Reordering must include every page exactly once")
        document.select(indexes)
        self._session.mark_dirty()

    def split(self, destination: str | Path, first: int, last: int) -> Path:
        document = self._session.document
        if not 0 <= first <= last < len(document):
            raise ValueError("Invalid page range")
        with fitz.open() as output:
            output.insert_pdf(document, from_page=first, to_page=last)
            output.save(destination)
        return Path(destination)
