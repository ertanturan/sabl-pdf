from pathlib import Path

import fitz

from sabl_pdf.core.session import DocumentSession


class SignatureService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def import_image(self, page_index: int, bounds: tuple[float, float, float, float], image: str | Path) -> None:
        path = Path(image)
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("Signature image must be PNG or JPEG")
        rect = fitz.Rect(bounds)
        if rect.is_empty or rect.is_infinite:
            raise ValueError("Select a valid signature area")
        self._session.document[page_index].insert_image(rect, filename=str(path), overlay=True)
        self._session.mark_dirty()

    def draw(self, page_index: int, bounds: tuple[float, float, float, float],
             strokes: list[list[tuple[float, float]]]) -> None:
        rect = fitz.Rect(bounds)
        if rect.is_empty or not strokes or not any(len(stroke) >= 2 for stroke in strokes):
            raise ValueError("Draw a signature before applying")
        page = self._session.document[page_index]
        for stroke in strokes:
            for start, end in zip(stroke, stroke[1:]):
                first = fitz.Point(rect.x0 + start[0] * rect.width, rect.y0 + start[1] * rect.height)
                last = fitz.Point(rect.x0 + end[0] * rect.width, rect.y0 + end[1] * rect.height)
                page.draw_line(first, last, color=(0, 0, 0), width=1.4, overlay=True)
        self._session.mark_dirty()
