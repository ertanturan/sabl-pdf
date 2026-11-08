from pathlib import Path
import re

import fitz

from sabl_pdf.core.session import DocumentSession


class SignatureService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def import_image(self, page_index: int, bounds: tuple[float, float, float, float], image: str | Path) -> int:
        path = Path(image)
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("Signature image must be PNG or JPEG")
        rect = self._valid_rect(bounds)
        source = fitz.Pixmap(str(path))
        pixmap = fitz.Pixmap(fitz.csRGB, source)
        page = self._session.document[page_index]
        stamp = page.add_stamp_annot(rect)
        image_xref = self._embed_image(pixmap)
        self._set_stamp_appearance(stamp, image_xref, pixmap.width, pixmap.height)
        stamp.set_rect(rect)
        self._session.mark_dirty()
        return stamp.xref

    def draw(self, page_index: int, bounds: tuple[float, float, float, float],
             strokes: list[list[tuple[float, float]]]) -> int:
        rect = self._valid_rect(bounds)
        if not any(len(stroke) >= 2 for stroke in strokes):
            raise ValueError("Draw a signature before applying")
        paths = [
            [(rect.x0 + x * rect.width, rect.y0 + y * rect.height) for x, y in stroke]
            for stroke in strokes if len(stroke) >= 2
        ]
        annotation = self._session.document[page_index].add_ink_annot(paths)
        annotation.set_colors(stroke=(0, 0, 0))
        annotation.set_border(width=1.4)
        annotation.update()
        self._session.mark_dirty()
        return annotation.xref

    def _valid_rect(self, bounds: tuple[float, float, float, float]) -> fitz.Rect:
        rect = fitz.Rect(bounds)
        if rect.is_empty or rect.is_infinite:
            raise ValueError("Select a valid signature area")
        return rect

    def _embed_image(self, pixmap: fitz.Pixmap) -> int:
        raw = pixmap.samples
        if pixmap.alpha:
            rgb = b"".join(raw[index:index + 3] for index in range(0, len(raw), 4))
            mask_xref = self._embed_image_stream(raw[3::4], pixmap.width, pixmap.height, "DeviceGray")
        else:
            rgb = raw
            mask_xref = None
        return self._embed_image_stream(rgb, pixmap.width, pixmap.height, "DeviceRGB", mask_xref)

    def _embed_image_stream(self, raw: bytes, width: int, height: int, color_space: str,
                            mask_xref: int | None = None) -> int:
        doc = self._session.document
        xref = doc.get_new_xref()
        mask = f" /SMask {mask_xref} 0 R" if mask_xref else ""
        doc.update_object(
            xref,
            f"<</Type /XObject /Subtype /Image /Width {width} /Height {height} "
            f"/ColorSpace /{color_space} /BitsPerComponent 8{mask}>>",
        )
        doc.update_stream(xref, raw)
        return xref

    def _set_stamp_appearance(self, stamp: fitz.Annot, xref: int, width: int, height: int) -> None:
        doc = self._session.document
        appearance = doc.xref_get_key(stamp.xref, "AP")[1]
        match = re.search(r"/N\s+(\d+)\s+0\s+R", appearance)
        if match is None:
            raise RuntimeError("Signature appearance is unavailable")
        appearance_xref = int(match.group(1))
        doc.xref_set_key(appearance_xref, "Resources", f"<</XObject <</Im0 {xref} 0 R>>>>")
        doc.xref_set_key(appearance_xref, "BBox", f"[0 0 {width} {height}]")
        doc.update_stream(
            appearance_xref, f"q\n{width} 0 0 {height} 0 0 cm\n/Im0 Do\nQ".encode()
        )
