from dataclasses import dataclass

import fitz

from sabl_pdf.core.session import DocumentSession


@dataclass(frozen=True)
class PlacedItem:
    page: int
    xref: int
    bounds: tuple[float, float, float, float]
    kind: str


class PlacedItemService:
    _SUPPORTED = {
        fitz.PDF_ANNOT_FREE_TEXT,
        fitz.PDF_ANNOT_INK,
        fitz.PDF_ANNOT_STAMP,
        fitz.PDF_ANNOT_HIGHLIGHT,
        fitz.PDF_ANNOT_UNDERLINE,
        fitz.PDF_ANNOT_TEXT,
    }

    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def list(self) -> list[PlacedItem]:
        result = []
        for index, page in enumerate(self._session.document):
            result.extend(
                PlacedItem(index, annot.xref, tuple(annot.rect), annot.type[1])
                for annot in page.annots() or ()
                if annot.type[0] in self._SUPPORTED
            )
        return result

    def move(self, page_index: int, xref: int, bounds: tuple[float, float, float, float]) -> int:
        page = self._session.document[page_index]
        annot = self._get(page, xref)
        new_rect = fitz.Rect(bounds)
        if new_rect.is_empty or new_rect.is_infinite or not page.rect.contains(new_rect):
            raise ValueError("Keep the item inside its page")
        if abs(new_rect.width - annot.rect.width) > 0.1 or abs(new_rect.height - annot.rect.height) > 0.1:
            raise ValueError("Moving an item cannot resize it")
        if annot.type[0] in {fitz.PDF_ANNOT_INK, fitz.PDF_ANNOT_HIGHLIGHT, fitz.PDF_ANNOT_UNDERLINE}:
            xref = self._move_vertex_annotation(page, annot, new_rect)
        else:
            annot.set_rect(new_rect)
        self._session.mark_dirty()
        return xref

    def delete(self, page_index: int, xref: int) -> None:
        page = self._session.document[page_index]
        page.delete_annot(self._get(page, xref))
        self._session.mark_dirty()

    def _get(self, page: fitz.Page, xref: int) -> fitz.Annot:
        annot = page.load_annot(xref)
        if annot is None or annot.type[0] not in self._SUPPORTED:
            raise ValueError("Placed item not found")
        return annot

    def _move_vertex_annotation(self, page: fitz.Page, annot: fitz.Annot, rect: fitz.Rect) -> int:
        dx, dy = rect.x0 - annot.rect.x0, rect.y0 - annot.rect.y0
        if annot.type[0] == fitz.PDF_ANNOT_INK:
            strokes = [[(x + dx, y + dy) for x, y in stroke] for stroke in annot.vertices]
            replacement = page.add_ink_annot(strokes)
        else:
            points = [fitz.Point(x + dx, y + dy) for x, y in annot.vertices]
            quads = [fitz.Quad(points[index:index + 4]) for index in range(0, len(points), 4)]
            factory = (page.add_highlight_annot if annot.type[0] == fitz.PDF_ANNOT_HIGHLIGHT
                       else page.add_underline_annot)
            replacement = factory(quads)
        self._copy_style(annot, replacement)
        new_xref = replacement.xref
        page.delete_annot(annot)
        return new_xref

    def _copy_style(self, source: fitz.Annot, target: fitz.Annot) -> None:
        stroke = source.colors.get("stroke")
        if stroke:
            target.set_colors(stroke=stroke)
        width = source.border.get("width")
        if width is not None:
            target.set_border(width=width)
        if source.opacity >= 0:
            target.set_opacity(source.opacity)
        target.update()
