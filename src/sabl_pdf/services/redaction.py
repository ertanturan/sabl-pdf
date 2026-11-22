from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import fitz
from PIL import Image, ImageDraw

from sabl_pdf.core.session import DocumentSession


@dataclass(frozen=True)
class RedactionTarget:
    page: int
    bounds: tuple[float, float, float, float]
    label: str = ""


@dataclass(frozen=True)
class RedactionReport:
    pages: int
    regions: int
    output: Path


class RedactionService:
    def __init__(self, session: DocumentSession) -> None:
        self._session = session

    def find(self, phrase: str) -> list[RedactionTarget]:
        if not phrase.strip():
            raise ValueError("Enter information to redact")
        self._check_source()
        matches: list[RedactionTarget] = []
        for index, page in enumerate(self._session.document):
            native = page.search_for(phrase)
            matches.extend(RedactionTarget(index, tuple(rect), phrase) for rect in native)
            if not page.get_text("text").strip() and page.get_images(full=True):
                try:
                    ocr = page.get_textpage_ocr(language="eng", full=True)
                    hits = page.search_for(phrase, textpage=ocr)
                except Exception as exc:
                    raise ValueError(
                        "A scanned page could not be searched with OCR. "
                        "Redact it by selecting an area instead."
                    ) from exc
                matches.extend(RedactionTarget(index, tuple(rect), phrase) for rect in hits)
        return matches

    def area_target(self, page_index: int, display_bounds: tuple) -> RedactionTarget:
        page = self._session.document[page_index]
        rect = fitz.Rect(display_bounds).normalize() * page.derotation_matrix
        return RedactionTarget(page_index, tuple(rect))

    def export(
        self, targets: list[RedactionTarget], destination: str | Path, scale: float = 2.0
    ) -> RedactionReport:
        self._check_source()
        self._validate(targets)
        if scale < 1 or scale > 4:
            raise ValueError("Invalid redaction resolution")
        output = Path(destination)
        if self._session.path and output.resolve() == self._session.path.resolve():
            raise ValueError("Redaction must save to a different file")
        if output.exists():
            raise FileExistsError("Choose a new filename for the redacted copy")
        if not output.parent.is_dir():
            raise ValueError("The destination folder does not exist")
        temporary: Path | None = None
        try:
            with fitz.open(stream=self._session.document.tobytes(), filetype="pdf") as working:
                self._apply(working, targets)
                with fitz.open() as result:
                    for page_index, page in enumerate(working):
                        image = self._render(page, targets, page_index, scale)
                        with BytesIO() as buffer:
                            image.save(buffer, format="PNG")
                            clean_page = result.new_page(
                                width=page.rect.width, height=page.rect.height
                            )
                            clean_page.insert_image(clean_page.rect, stream=buffer.getvalue())
                    with NamedTemporaryFile(
                        suffix=".pdf", prefix=".sabl-redaction-", dir=output.parent,
                        delete=False,
                    ) as handle:
                        temporary = Path(handle.name)
                    result.save(temporary, garbage=4, deflate=True)
            self._verify(temporary, targets)
            if output.exists():
                raise FileExistsError("The destination was created during redaction")
            temporary.rename(output)
            temporary = None
            return RedactionReport(len(self._session.document), len(targets), output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _check_source(self) -> None:
        document = self._session.document
        if document.is_encrypted or document.needs_pass:
            raise ValueError("Protected PDFs are not supported for secure redaction")
        if document.get_sigflags() or document.is_repaired or self._session.open_warnings:
            raise ValueError("Signed or damaged PDFs cannot be safely redacted")

    def _validate(self, targets: list[RedactionTarget]) -> None:
        if not targets:
            raise ValueError("Select at least one region to redact")
        document = self._session.document
        for target in targets:
            if not 0 <= target.page < len(document):
                raise ValueError("A redaction references an invalid page")
            bounds = fitz.Rect(target.bounds)
            if bounds.is_empty or bounds.is_infinite:
                raise ValueError("A redaction region is empty or invalid")
            if not document[target.page].rect.intersects(bounds):
                raise ValueError("A redaction region is outside its page")

    def _apply(self, document: fitz.Document, targets: list[RedactionTarget]) -> None:
        touched = set()
        for target in targets:
            document[target.page].add_redact_annot(
                fitz.Rect(target.bounds), fill=(0, 0, 0), cross_out=False
            )
            touched.add(target.page)
        for index in sorted(touched):
            document[index].apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_REMOVE,
                graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
                text=fitz.PDF_REDACT_TEXT_REMOVE,
            )

    def _render(
        self, page: fitz.Page, targets: list[RedactionTarget], page_index: int, scale: float
    ) -> Image.Image:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False, annots=True)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        draw = ImageDraw.Draw(image)
        for target in targets:
            if target.page != page_index:
                continue
            rect = fitz.Rect(target.bounds) * page.rotation_matrix
            x_scale = image.width / page.rect.width
            y_scale = image.height / page.rect.height
            rectangle = (
                max(0, int(rect.x0 * x_scale) - 3),
                max(0, int(rect.y0 * y_scale) - 3),
                min(image.width - 1, int(rect.x1 * x_scale) + 3),
                min(image.height - 1, int(rect.y1 * y_scale) + 3),
            )
            draw.rectangle(rectangle, fill=(0, 0, 0))
        return image

    def _verify(self, candidate: Path, targets: list[RedactionTarget]) -> None:
        with fitz.open(candidate) as document:
            if len(document) != len(self._session.document):
                raise RuntimeError("Redaction verification failed: page count")
            if document.embfile_count() or document.get_sigflags():
                raise RuntimeError("Redaction verification failed: active PDF objects")
            for index, page in enumerate(document):
                if page.get_text("text").strip() or page.get_links():
                    raise RuntimeError("Redaction verification failed: surviving text or links")
                if list(page.annots() or ()) or list(page.widgets() or ()):
                    raise RuntimeError("Redaction verification failed: annotations or fields")
                images = page.get_images(full=True)
                if len(images) != 1:
                    raise RuntimeError("Redaction verification failed: image-only structure")
                self._verify_pixels(document, page, targets, index, images[0][0])

    def _verify_pixels(
        self, document: fitz.Document, page: fitz.Page,
        targets: list[RedactionTarget], index: int, xref: int,
    ) -> None:
        with Image.open(BytesIO(document.extract_image(xref)["image"])) as source:
            image = source.convert("RGB")
            for target in targets:
                if target.page != index:
                    continue
                rect = fitz.Rect(target.bounds) * page.rotation_matrix
                center_x = max(0, min(image.width - 1, round(
                    (rect.x0 + rect.x1) / 2 * image.width / page.rect.width
                )))
                center_y = max(0, min(image.height - 1, round(
                    (rect.y0 + rect.y1) / 2 * image.height / page.rect.height
                )))
                if image.getpixel((center_x, center_y)) != (0, 0, 0):
                    raise RuntimeError("Redaction verification failed: uncovered pixels")
