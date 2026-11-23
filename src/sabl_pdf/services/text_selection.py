from dataclasses import dataclass

import fitz

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.ocr_text import OcrTextPages


@dataclass(frozen=True)
class TextGlyph:
    character: str
    line: int
    bounds: tuple[float, float, float, float]


@dataclass(frozen=True)
class TextSelection:
    page: int
    text: str
    rects: tuple[tuple[float, float, float, float], ...]
    display_rects: tuple[tuple[float, float, float, float], ...]


class TextSelectionService:
    def __init__(
        self, session: DocumentSession, ocr_pages: OcrTextPages | None = None
    ) -> None:
        self._session = session
        self._ocr_pages = ocr_pages or OcrTextPages(session)

    def select(
        self,
        page_index: int,
        start: tuple[float, float],
        end: tuple[float, float],
    ) -> TextSelection | None:
        page = self._session.document[page_index]
        glyphs = self._glyphs(page)
        source = fitz.Point(start) * page.derotation_matrix
        target = fitz.Point(end) * page.derotation_matrix
        first = self._caret(glyphs, source, require_near=True) if glyphs else None
        if first is None and self._ocr_pages.is_candidate(page):
            ocr_page, textpage = self._ocr_pages.get(page_index)
            glyphs = self._glyphs(ocr_page, textpage)
            first = self._caret(glyphs, source, require_near=True) if glyphs else None
        if first is None:
            return None
        last = self._caret(glyphs, target, require_near=False)
        if first is None or last is None or first == last:
            return None
        selected = glyphs[min(first, last):max(first, last)]
        rects = self._line_rects(selected)
        display = tuple(self._bounds(fitz.Rect(rect) * page.rotation_matrix) for rect in rects)
        return TextSelection(page_index, self._text(selected), rects, display)

    def _glyphs(
        self, page: fitz.Page, textpage: fitz.TextPage | None = None
    ) -> list[TextGlyph]:
        glyphs: list[TextGlyph] = []
        line_number = 0
        raw = page.get_text("rawdict", textpage=textpage)
        if not isinstance(raw, dict):
            raise ValueError("Cannot extract PDF character geometry")
        for block in raw["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    for character in span["chars"]:
                        bounds = tuple(character["bbox"])
                        if fitz.Rect(bounds).is_empty:
                            continue
                        glyphs.append(TextGlyph(character["c"], line_number, bounds))
                line_number += 1
        return glyphs

    def _caret(
        self, glyphs: list[TextGlyph], point: fitz.Point, require_near: bool
    ) -> int | None:
        def distance(glyph: TextGlyph) -> float:
            rect = fitz.Rect(glyph.bounds)
            return max(rect.x0 - point.x, 0, point.x - rect.x1) ** 2 + max(
                rect.y0 - point.y, 0, point.y - rect.y1
            ) ** 2

        index = min(range(len(glyphs)), key=lambda item: distance(glyphs[item]))
        if require_near and distance(glyphs[index]) > 100:
            return None
        bounds = fitz.Rect(glyphs[index].bounds)
        after = point.x >= (bounds.x0 + bounds.x1) / 2
        return index + int(after)

    def _line_rects(
        self, glyphs: list[TextGlyph]
    ) -> tuple[tuple[float, float, float, float], ...]:
        rectangles: list[fitz.Rect] = []
        previous_line: int | None = None
        for glyph in glyphs:
            bounds = fitz.Rect(glyph.bounds)
            if glyph.line == previous_line:
                rectangles[-1] |= bounds
            else:
                rectangles.append(bounds)
                previous_line = glyph.line
        return tuple(self._bounds(rect) for rect in rectangles)

    def _bounds(self, rect: fitz.Rect) -> tuple[float, float, float, float]:
        return (rect.x0, rect.y0, rect.x1, rect.y1)

    def _text(self, glyphs: list[TextGlyph]) -> str:
        parts: list[str] = []
        previous_line: int | None = None
        for glyph in glyphs:
            if previous_line is not None and glyph.line != previous_line:
                parts.append("\n")
            parts.append(glyph.character)
            previous_line = glyph.line
        return "".join(parts)
