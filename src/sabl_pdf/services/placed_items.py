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

    def move(
        self, page_index: int, xref: int, bounds: tuple[float, float, float, float],
        target_page_index: int | None = None,
    ) -> int:
        document = self._session.document
        source = document[page_index]
        target_index = page_index if target_page_index is None else target_page_index
        target = document[target_index]
        annot = self._get(source, xref)
        new_rect = self._validate_move(annot, target, bounds)
        if annot.type[0] in {
            fitz.PDF_ANNOT_INK, fitz.PDF_ANNOT_HIGHLIGHT, fitz.PDF_ANNOT_UNDERLINE,
        }:
            new_xref = self._move_vertex_annotation(source, target, annot, new_rect)
        elif target_index != page_index:
            new_xref = self._transfer_annotation(source, target, annot, new_rect)
        else:
            annot.set_rect(new_rect)
            new_xref = xref
        self._session.mark_dirty()
        return new_xref

    def _validate_move(self, annot: fitz.Annot, target: fitz.Page, bounds: tuple) -> fitz.Rect:
        rect = fitz.Rect(bounds)
        if rect.is_empty or rect.is_infinite or not target.rect.contains(rect):
            raise ValueError("Keep the item inside its page")
        if abs(rect.width - annot.rect.width) > 0.1 or abs(rect.height - annot.rect.height) > 0.1:
            raise ValueError("Moving an item cannot resize it")
        return rect

    def _transfer_annotation(
        self, source: fitz.Page, target: fitz.Page, annot: fitz.Annot, bounds: fitz.Rect,
    ) -> int:
        replacement = self._create_placeholder(target, annot, bounds)
        xref = replacement.xref
        document = self._session.document
        try:
            document.update_object(xref, document.xref_object(annot.xref))
            document.xref_set_key(xref, "P", f"{target.xref} 0 R")
            document.xref_set_key(xref, "NM", fitz.get_pdf_str(f"sabl-moved-{xref}"))
            target.load_annot(xref).set_rect(bounds)
        except Exception:
            target.delete_annot(replacement)
            raise
        source.delete_annot(annot)
        return xref

    def _create_placeholder(
        self, page: fitz.Page, annot: fitz.Annot, bounds: fitz.Rect,
    ) -> fitz.Annot:
        kind = annot.type[0]
        if kind == fitz.PDF_ANNOT_FREE_TEXT:
            return page.add_freetext_annot(bounds, annot.info.get("content", ""))
        if kind == fitz.PDF_ANNOT_STAMP:
            return page.add_stamp_annot(bounds)
        if kind == fitz.PDF_ANNOT_TEXT:
            return page.add_text_annot(bounds.tl, annot.info.get("content", ""))
        raise ValueError("This item cannot be moved between pages")

    def delete(self, page_index: int, xref: int) -> None:
        page = self._session.document[page_index]
        page.delete_annot(self._get(page, xref))
        self._session.mark_dirty()

    def _get(self, page: fitz.Page, xref: int) -> fitz.Annot:
        annot = page.load_annot(xref)
        if annot is None or annot.type[0] not in self._SUPPORTED:
            raise ValueError("Placed item not found")
        return annot

    def _move_vertex_annotation(
        self, source: fitz.Page, target: fitz.Page, annot: fitz.Annot, rect: fitz.Rect,
    ) -> int:
        dx, dy = rect.x0 - annot.rect.x0, rect.y0 - annot.rect.y0
        if annot.type[0] == fitz.PDF_ANNOT_INK:
            strokes = [[(x + dx, y + dy) for x, y in stroke] for stroke in annot.vertices]
            replacement = target.add_ink_annot(strokes)
        else:
            points = [fitz.Point(x + dx, y + dy) for x, y in annot.vertices]
            quads = [fitz.Quad(points[index:index + 4]) for index in range(0, len(points), 4)]
            factory = (target.add_highlight_annot if annot.type[0] == fitz.PDF_ANNOT_HIGHLIGHT
                       else target.add_underline_annot)
            replacement = factory(quads)
        self._copy_style(annot, replacement)
        new_xref = replacement.xref
        source.delete_annot(annot)
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
